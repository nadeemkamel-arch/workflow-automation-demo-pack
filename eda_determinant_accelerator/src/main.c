#include <ctype.h>
#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern int64_t detn_i64(int64_t *matrix, int64_t n);

typedef struct {
    int64_t *values;
    size_t n;
} Matrix;

typedef struct {
    const char *name;
    const int64_t *matrix;
    size_t n;
    int64_t expected;
} DetCase;

static const int64_t case_1x1[] = {
    7,
};

static const int64_t case_2x2_basic[] = {
    1, 2,
    3, 4,
};

static const int64_t case_2x2_diagonal[] = {
    5, 0,
    0, 5,
};

static const int64_t case_2x2_singular[] = {
    2, 3,
    4, 6,
};

static const int64_t case_2x2_negative[] = {
    -1, 2,
    3, -4,
};

static const int64_t case_3x3[] = {
    1, 2, 3,
    0, 1, 4,
    5, 6, 0,
};

static const int64_t case_3x3_singular[] = {
    1, 2, 3,
    2, 4, 6,
    7, 8, 9,
};

static const int64_t case_3x3_pivot_swap[] = {
    0, 2, 1,
    1, 0, 3,
    4, 5, 6,
};

static const int64_t case_4x4_identity[] = {
    1, 0, 0, 0,
    0, 1, 0, 0,
    0, 0, 1, 0,
    0, 0, 0, 1,
};

static const int64_t case_4x4_triangular[] = {
    2, 1, 3, 4,
    0, 3, 5, 6,
    0, 0, -2, 7,
    0, 0, 0, 4,
};

static void free_matrix(Matrix *matrix) {
    free(matrix->values);
    matrix->values = NULL;
    matrix->n = 0;
}

static void print_usage(void) {
    printf("Usage:\n");
    printf("  ./det 1 2, 3 4\n");
    printf("  ./det \"1 2 3, 4 5 6, 7 8 9\"\n");
    printf("\nRows are separated by commas:\n");
    printf("  1 2 3,\n");
    printf("  4 5 6,\n");
    printf("  7 8 9\n");
}

static void print_matrix(const int64_t *matrix, size_t n) {
    for (size_t row = 0; row < n; row++) {
        printf("  ");
        for (size_t col = 0; col < n; col++) {
            if (col > 0) {
                printf(" ");
            }
            printf("%" PRId64, matrix[row * n + col]);
        }
        printf("\n");
    }
}

static char *join_args(int argc, char **argv) {
    size_t total = 1;

    for (int i = 1; i < argc; i++) {
        const size_t arg_len = strlen(argv[i]);
        if (arg_len > SIZE_MAX - total - 1) {
            return NULL;
        }
        total += arg_len + 1;
    }

    char *input = malloc(total);
    if (input == NULL) {
        return NULL;
    }

    input[0] = '\0';
    for (int i = 1; i < argc; i++) {
        if (i > 1) {
            strcat(input, " ");
        }
        strcat(input, argv[i]);
    }

    return input;
}

static bool append_value(int64_t **values,
                         size_t *count,
                         size_t *capacity,
                         int64_t value,
                         const char **error) {
    if (*count == *capacity) {
        const size_t next_capacity = *capacity == 0 ? 16 : *capacity * 2;
        if (next_capacity < *capacity || next_capacity > SIZE_MAX / sizeof(**values)) {
            *error = "matrix is too large";
            return false;
        }

        int64_t *next = realloc(*values, next_capacity * sizeof(**values));
        if (next == NULL) {
            *error = "could not allocate matrix storage";
            return false;
        }

        *values = next;
        *capacity = next_capacity;
    }

    (*values)[*count] = value;
    (*count)++;
    return true;
}

static bool finish_row(size_t current_cols,
                       size_t *expected_cols,
                       size_t *row_count,
                       const char **error) {
    if (current_cols == 0) {
        *error = "empty rows are not allowed";
        return false;
    }

    if (*expected_cols == 0) {
        *expected_cols = current_cols;
    } else if (current_cols != *expected_cols) {
        *error = "every row must contain the same number of values";
        return false;
    }

    (*row_count)++;
    return true;
}

static bool parse_matrix_input(const char *input, Matrix *out, const char **error) {
    const char *p = input;
    int64_t *values = NULL;
    size_t count = 0;
    size_t capacity = 0;
    size_t current_cols = 0;
    size_t expected_cols = 0;
    size_t row_count = 0;
    bool saw_value = false;
    bool ended_with_comma = false;

    out->values = NULL;
    out->n = 0;

    while (*p != '\0') {
        while (isspace((unsigned char)*p)) {
            p++;
        }

        if (*p == '\0') {
            break;
        }

        if (*p == ',') {
            if (!finish_row(current_cols, &expected_cols, &row_count, error)) {
                free(values);
                return false;
            }
            current_cols = 0;
            ended_with_comma = true;
            p++;
            continue;
        }

        errno = 0;
        char *end = NULL;
        const intmax_t parsed = strtoimax(p, &end, 10);

        if (p == end) {
            *error = "expected an integer or comma";
            free(values);
            return false;
        }
        if (errno == ERANGE || parsed < INT64_MIN || parsed > INT64_MAX) {
            *error = "integer is outside the int64 range";
            free(values);
            return false;
        }
        if (!append_value(&values, &count, &capacity, (int64_t)parsed, error)) {
            free(values);
            return false;
        }

        saw_value = true;
        ended_with_comma = false;
        current_cols++;
        p = end;
    }

    if (!saw_value) {
        *error = "provide at least one integer";
        free(values);
        return false;
    }
    if (ended_with_comma) {
        *error = "trailing comma creates an empty row";
        free(values);
        return false;
    }
    if (!finish_row(current_cols, &expected_cols, &row_count, error)) {
        free(values);
        return false;
    }
    if (row_count != expected_cols) {
        *error = "matrix must be square; use commas to separate rows";
        free(values);
        return false;
    }
    if (expected_cols > (size_t)INT64_MAX) {
        *error = "matrix dimension is too large";
        free(values);
        return false;
    }
    if (expected_cols != 0 && count / expected_cols != row_count) {
        *error = "matrix size overflow";
        free(values);
        return false;
    }

    out->values = values;
    out->n = expected_cols;
    return true;
}

static bool determinant_from_copy(const int64_t *matrix,
                                  size_t n,
                                  int64_t *determinant,
                                  const char **error) {
    if (n == 0) {
        *error = "matrix dimension must be at least one";
        return false;
    }
    if (n > SIZE_MAX / n || n * n > SIZE_MAX / sizeof(*matrix)) {
        *error = "matrix is too large";
        return false;
    }

    const size_t count = n * n;
    int64_t *work = malloc(count * sizeof(*work));
    if (work == NULL) {
        *error = "could not allocate working matrix";
        return false;
    }

    memcpy(work, matrix, count * sizeof(*work));
    *determinant = detn_i64(work, (int64_t)n);
    free(work);
    return true;
}

static int run_cli_matrix(int argc, char **argv) {
    Matrix matrix = {0};
    const char *error = NULL;
    char *input = join_args(argc, argv);

    if (input == NULL) {
        fprintf(stderr, "error: could not allocate input buffer\n");
        return 1;
    }

    if (!parse_matrix_input(input, &matrix, &error)) {
        fprintf(stderr, "error: %s\n\n", error);
        print_usage();
        free(input);
        return 1;
    }

    int64_t determinant = 0;
    if (!determinant_from_copy(matrix.values, matrix.n, &determinant, &error)) {
        fprintf(stderr, "error: %s\n", error);
        free(input);
        free_matrix(&matrix);
        return 1;
    }

    printf("Matrix:\n");
    print_matrix(matrix.values, matrix.n);
    printf("\nDeterminant: %" PRId64 "\n", determinant);

    free(input);
    free_matrix(&matrix);
    return 0;
}

static bool expect_parse_failure(const char *input) {
    Matrix matrix = {0};
    const char *error = NULL;
    const bool parsed = parse_matrix_input(input, &matrix, &error);
    free_matrix(&matrix);
    return !parsed && error != NULL;
}

static int run_demo_cases(void) {
    const DetCase cases[] = {
        {"1x1", case_1x1, 1, 7},
        {"2x2 basic", case_2x2_basic, 2, -2},
        {"2x2 diagonal", case_2x2_diagonal, 2, 25},
        {"2x2 singular", case_2x2_singular, 2, 0},
        {"2x2 negative values", case_2x2_negative, 2, -2},
        {"3x3", case_3x3, 3, 1},
        {"3x3 singular", case_3x3_singular, 3, 0},
        {"3x3 pivot swap", case_3x3_pivot_swap, 3, 17},
        {"4x4 identity", case_4x4_identity, 4, 1},
        {"4x4 triangular", case_4x4_triangular, 4, -48},
    };
    const char *parser_failures[] = {
        "",
        "1 2 3 4",
        "1 2, 3",
        "1 x, 2 3",
    };
    const size_t case_count = sizeof(cases) / sizeof(cases[0]);
    const size_t parser_failure_count = sizeof(parser_failures) / sizeof(parser_failures[0]);
    size_t failures = 0;

    for (size_t i = 0; i < case_count; i++) {
        const char *error = NULL;
        int64_t actual = 0;
        const bool computed = determinant_from_copy(cases[i].matrix, cases[i].n, &actual, &error);
        const int passed = computed && actual == cases[i].expected;

        printf("%s (%zux%zu): actual=%" PRId64 ", expected=%" PRId64 " [%s]\n",
               cases[i].name,
               cases[i].n,
               cases[i].n,
               actual,
               cases[i].expected,
               passed ? "PASS" : "FAIL");

        if (!passed) {
            if (error != NULL) {
                printf("  error: %s\n", error);
            }
            failures++;
        }
    }

    for (size_t i = 0; i < parser_failure_count; i++) {
        const bool passed = expect_parse_failure(parser_failures[i]);
        printf("parser rejects \"%s\" [%s]\n",
               parser_failures[i],
               passed ? "PASS" : "FAIL");
        if (!passed) {
            failures++;
        }
    }

    printf("\n%zu/%zu checks passed.\n",
           case_count + parser_failure_count - failures,
           case_count + parser_failure_count);
    return failures == 0 ? 0 : 1;
}

int main(int argc, char **argv) {
    if (argc > 1) {
        return run_cli_matrix(argc, argv);
    }

    printf("No matrix provided, running built-in checks.\n\n");
    print_usage();
    printf("\n");
    return run_demo_cases();
}
