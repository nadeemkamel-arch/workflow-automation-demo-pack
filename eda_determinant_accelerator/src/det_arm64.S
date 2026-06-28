.text
.align 2

.globl _det2_i64
_det2_i64:
    ldr x1, [x0]        // a
    ldr x2, [x0, #8]    // b
    ldr x3, [x0, #16]   // c
    ldr x4, [x0, #24]   // d

    mul x5, x1, x4      // a * d
    mul x6, x2, x3      // b * c
    sub x0, x5, x6      // a * d - b * c
    ret

.globl _detn_i64
_detn_i64:
    cmp x1, #0
    b.gt Ldetn_positive
    mov x0, #0
    ret

Ldetn_positive:
    cmp x1, #1
    b.ne Ldetn_check_2
    ldr x0, [x0]
    ret

Ldetn_check_2:
    cmp x1, #2
    b.ne Ldetn_general
    b _det2_i64

Ldetn_general:
    stp x29, x30, [sp, #-96]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    stp x21, x22, [sp, #32]
    stp x23, x24, [sp, #48]
    stp x25, x26, [sp, #64]
    stp x27, x28, [sp, #80]

    mov x19, x0         // matrix base
    mov x20, x1         // n
    mov x21, #0         // k
    mov x22, #1         // determinant sign
    mov x24, #1         // previous pivot
    sub x25, x20, #1    // final pivot index

Ldetn_outer:
    cmp x21, x25
    b.ge Ldetn_done

    mul x8, x21, x20
    add x8, x8, x21
    ldr x23, [x19, x8, lsl #3] // pivot = a[k][k]
    cbnz x23, Ldetn_pivot_ready

    add x26, x21, #1    // candidate swap row

Ldetn_find_swap:
    cmp x26, x20
    b.ge Ldetn_singular
    mul x8, x26, x20
    add x8, x8, x21
    ldr x9, [x19, x8, lsl #3]
    cbnz x9, Ldetn_swap_rows
    add x26, x26, #1
    b Ldetn_find_swap

Ldetn_swap_rows:
    mov x27, #0         // column

Ldetn_swap_loop:
    cmp x27, x20
    b.ge Ldetn_swap_done

    mul x8, x21, x20
    add x8, x8, x27
    add x8, x19, x8, lsl #3

    mul x9, x26, x20
    add x9, x9, x27
    add x9, x19, x9, lsl #3

    ldr x10, [x8]
    ldr x11, [x9]
    str x11, [x8]
    str x10, [x9]

    add x27, x27, #1
    b Ldetn_swap_loop

Ldetn_swap_done:
    neg x22, x22
    mul x8, x21, x20
    add x8, x8, x21
    ldr x23, [x19, x8, lsl #3]

Ldetn_pivot_ready:
    add x26, x21, #1    // i

Ldetn_i_loop:
    cmp x26, x20
    b.ge Ldetn_finish_k

    mul x11, x26, x20   // row i base index
    add x8, x11, x21
    ldr x13, [x19, x8, lsl #3] // a[i][k]

    mul x12, x21, x20   // row k base index
    add x27, x21, #1    // j

Ldetn_j_loop:
    cmp x27, x20
    b.ge Ldetn_next_i

    add x8, x11, x27
    ldr x9, [x19, x8, lsl #3]  // a[i][j]

    add x14, x12, x27
    ldr x15, [x19, x14, lsl #3] // a[k][j]

    mul x9, x9, x23
    mul x15, x13, x15
    sub x9, x9, x15
    sdiv x9, x9, x24
    str x9, [x19, x8, lsl #3]

    add x27, x27, #1
    b Ldetn_j_loop

Ldetn_next_i:
    add x26, x26, #1
    b Ldetn_i_loop

Ldetn_finish_k:
    mov x24, x23
    add x21, x21, #1
    b Ldetn_outer

Ldetn_singular:
    mov x0, #0
    b Ldetn_epilogue

Ldetn_done:
    sub x8, x20, #1
    mul x9, x8, x20
    add x9, x9, x8
    ldr x0, [x19, x9, lsl #3]
    mul x0, x0, x22

Ldetn_epilogue:
    ldp x27, x28, [sp, #80]
    ldp x25, x26, [sp, #64]
    ldp x23, x24, [sp, #48]
    ldp x21, x22, [sp, #32]
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #96
    ret
