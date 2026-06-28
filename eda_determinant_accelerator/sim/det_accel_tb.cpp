#include "Vdet_accel.h"
#include "verilated.h"
#include "verilated_vcd_c.h"

#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <string>
#include <vector>

namespace {

struct MatrixCase {
    std::string name;
    int n;
    std::vector<int64_t> values;
};

struct RunResult {
    MatrixCase test;
    int64_t expected = 0;
    int64_t actual = 0;
    bool dut_error = false;
    bool passed = false;
    uint64_t cycles = 0;
};

int64_t golden_det(std::vector<int64_t> matrix, int n) {
    if (n <= 0) {
        return 0;
    }
    if (n == 1) {
        return matrix[0];
    }
    if (n == 2) {
        return matrix[0] * matrix[3] - matrix[1] * matrix[2];
    }

    int64_t sign = 1;
    int64_t previous_pivot = 1;

    for (int k = 0; k < n - 1; k++) {
        int64_t pivot = matrix[k * n + k];
        if (pivot == 0) {
            int swap_row = k + 1;
            while (swap_row < n && matrix[swap_row * n + k] == 0) {
                swap_row++;
            }
            if (swap_row == n) {
                return 0;
            }

            for (int col = 0; col < n; col++) {
                std::swap(matrix[k * n + col], matrix[swap_row * n + col]);
            }
            sign = -sign;
            pivot = matrix[k * n + k];
        }

        for (int row = k + 1; row < n; row++) {
            const int64_t aik = matrix[row * n + k];
            for (int col = k + 1; col < n; col++) {
                const int64_t numerator =
                    matrix[row * n + col] * pivot - aik * matrix[k * n + col];
                matrix[row * n + col] = numerator / previous_pivot;
            }
        }

        previous_pivot = pivot;
    }

    return sign * matrix[(n - 1) * n + (n - 1)];
}

class DetAccelSim {
  public:
    DetAccelSim() {
        Verilated::traceEverOn(true);
        dut_.trace(&trace_, 99);
        trace_.open("reports/waves/det_accel.vcd");
    }

    ~DetAccelSim() {
        dut_.final();
        trace_.close();
    }

    RunResult run(const MatrixCase &test) {
        reset();

        const uint64_t start_cycle = cycles_;
        dut_.n = static_cast<uint8_t>(test.n);
        dut_.start = 1;
        tick();
        dut_.start = 0;

        for (int64_t value : test.values) {
            while (!dut_.in_ready) {
                tick();
            }

            dut_.in_valid = 1;
            dut_.in_data = static_cast<uint16_t>(value);
            tick();
            dut_.in_valid = 0;
        }

        int guard = 20000;
        while (!dut_.out_valid && guard-- > 0) {
            tick();
        }

        RunResult result;
        result.test = test;
        result.expected = golden_det(test.values, test.n);
        result.actual = static_cast<int64_t>(dut_.det);
        result.dut_error = dut_.error;
        result.cycles = cycles_ - start_cycle;
        result.passed = dut_.out_valid && !dut_.error && result.actual == result.expected;

        tick();
        return result;
    }

  private:
    void reset() {
        dut_.clk = 0;
        dut_.rst_n = 0;
        dut_.start = 0;
        dut_.n = 0;
        dut_.in_valid = 0;
        dut_.in_data = 0;
        dut_.out_ready = 1;

        for (int i = 0; i < 4; i++) {
            tick();
        }

        dut_.rst_n = 1;
        tick();
    }

    void tick() {
        dut_.clk = 0;
        dut_.eval();
        trace_.dump(time_++);

        dut_.clk = 1;
        dut_.eval();
        trace_.dump(time_++);

        dut_.clk = 0;
        dut_.eval();
        trace_.dump(time_++);

        cycles_++;
    }

    Vdet_accel dut_;
    VerilatedVcdC trace_;
    vluint64_t time_ = 0;
    uint64_t cycles_ = 0;
};

std::vector<MatrixCase> directed_cases() {
    return {
        {"1x1 scalar", 1, {7}},
        {"2x2 fast path", 2, {1, 2, 3, 4}},
        {"2x2 negative", 2, {-1, 2, 3, -4}},
        {"3x3 normal", 3, {1, 2, 3, 0, 1, 4, 5, 6, 0}},
        {"3x3 singular", 3, {1, 2, 3, 2, 4, 6, 7, 8, 9}},
        {"3x3 pivot swap", 3, {0, 2, 1, 1, 0, 3, 4, 5, 6}},
        {"4x4 identity", 4, {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1}},
        {"4x4 triangular", 4, {2, 1, 3, 4, 0, 3, 5, 6, 0, 0, -2, 7, 0, 0, 0, 4}},
    };
}

std::vector<MatrixCase> random_cases() {
    std::vector<MatrixCase> cases;
    std::mt19937 rng(0xD37ACCEL);
    std::uniform_int_distribution<int> dist(-5, 5);

    for (int n = 1; n <= 4; n++) {
        for (int test_index = 0; test_index < 25; test_index++) {
            MatrixCase test;
            test.name = "random " + std::to_string(n) + "x" + std::to_string(n) +
                        " #" + std::to_string(test_index);
            test.n = n;
            test.values.reserve(static_cast<size_t>(n * n));

            for (int i = 0; i < n * n; i++) {
                test.values.push_back(dist(rng));
            }

            cases.push_back(test);
        }
    }

    return cases;
}

void write_reports(const std::vector<RunResult> &results) {
    std::ofstream summary("reports/sim_summary.md");
    std::ofstream latency("reports/latency.csv");

    summary << "# Simulation Summary\n\n";
    summary << "Generated by `make sim` using Verilator.\n\n";
    summary << "| Test | n | Expected | RTL | Cycles | Result |\n";
    summary << "| --- | ---: | ---: | ---: | ---: | --- |\n";

    latency << "test,n,expected,actual,cycles,passed\n";

    for (const RunResult &result : results) {
        summary << "| " << result.test.name
                << " | " << result.test.n
                << " | " << result.expected
                << " | " << result.actual
                << " | " << result.cycles
                << " | " << (result.passed ? "PASS" : "FAIL")
                << " |\n";

        latency << '"' << result.test.name << '"' << ','
                << result.test.n << ','
                << result.expected << ','
                << result.actual << ','
                << result.cycles << ','
                << (result.passed ? "PASS" : "FAIL") << '\n';
    }
}

} // namespace

int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    std::filesystem::create_directories("reports/waves");

    std::vector<MatrixCase> tests = directed_cases();
    std::vector<MatrixCase> random = random_cases();
    tests.insert(tests.end(), random.begin(), random.end());

    DetAccelSim sim;
    std::vector<RunResult> results;
    results.reserve(tests.size());

    size_t failures = 0;
    for (const MatrixCase &test : tests) {
        RunResult result = sim.run(test);
        if (!result.passed) {
            failures++;
        }
        std::cout << std::left << std::setw(22) << test.name
                  << " n=" << test.n
                  << " expected=" << result.expected
                  << " rtl=" << result.actual
                  << " cycles=" << result.cycles
                  << " " << (result.passed ? "PASS" : "FAIL") << "\n";
        results.push_back(result);
    }

    write_reports(results);

    std::cout << "\n" << (results.size() - failures) << "/" << results.size()
              << " RTL simulation cases passed.\n";
    return failures == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
