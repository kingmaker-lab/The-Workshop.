# Linux x86-64. Entrada: quadro little-endian de 16 bytes, seguido de EOF.
# A saída do processo é o veredito. Erros de transporte e formato retornam 64.
.section .bss
.lcomm frame, 16
.lcomm extra, 1

.section .text
.global _start
_start:
    lea frame(%rip), %rsi
    mov $16, %edx
read_frame:
    xor %eax, %eax                  # SYS_read
    xor %edi, %edi                  # stdin
    syscall
    cmp $-4, %rax                   # EINTR
    je read_frame
    test %rax, %rax
    jle malformed
    add %rax, %rsi
    sub %rax, %rdx
    jne read_frame

read_tail:
    xor %eax, %eax
    xor %edi, %edi
    lea extra(%rip), %rsi
    mov $1, %edx
    syscall
    cmp $-4, %rax
    je read_tail
    test %rax, %rax
    jne malformed

    lea frame(%rip), %rsi
    cmpl $1, (%rsi)
    je admission
    cmpl $2, (%rsi)
    je recovery
    jmp malformed

admission:
    # [op, maintenance, active, limit]
    mov 12(%rsi), %ecx
    test %ecx, %ecx
    jz malformed
    cmp $10000, %ecx
    ja malformed
    cmpl $1, 4(%rsi)
    ja malformed
    je reject_one                   # manutenção
    cmp %ecx, 8(%rsi)
    jae reject_two                  # capacidade atingida
    jmp accept

recovery:
    # [op, current, expected, target]
    mov 4(%rsi), %ecx
    cmp %ecx, 8(%rsi)
    jne reject_one                  # geração obsoleta
    cmp %ecx, 12(%rsi)
    jae reject_two                  # origem precisa ser anterior
    cmp $-1, %ecx
    je exhausted                    # incremento extrapolaria uint32

accept:
    xor %edi, %edi
    jmp exit
reject_one:
    mov $1, %edi
    jmp exit
reject_two:
    mov $2, %edi
    jmp exit
exhausted:
    mov $3, %edi
    jmp exit
malformed:
    mov $64, %edi
exit:
    mov $60, %eax                   # SYS_exit
    syscall

.section .note.GNU-stack,"",@progbits
