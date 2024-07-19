# Generate instruction mapping
cargo run --manifest-path ./BitVMX-CPU-Internal/Cargo.toml -p emulator -- instruction-mapping > ./execution_files/instruction_mapping.txt
# Generate instruction commitment
cargo run --manifest-path ./BitVMX-CPU-Internal/Cargo.toml -p emulator -- generate-rom-commitment --elf ./BitVMX-CPU-Internal/docker-riscv32/plainc.elf > ./execution_files/instruction_commitment.txt

cargo run --manifest-path ./BitVMX-CPU-Internal/Cargo.toml -p emulator -- execute --elf docker-riscv32/plainc.elf --input 01 -t > ./verifier_files/execution_trace.txt
cargo run --manifest-path ./BitVMX-CPU-Internal/Cargo.toml -p emulator -- execute --elf docker-riscv32/plainc.elf --input 01 -t > ./prober_files/execution_trace.txt