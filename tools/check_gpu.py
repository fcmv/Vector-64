"""Check the training environment; installation is documented in docs/nnue-training.md."""

import time

import torch


def check_gpu() -> int:
    print(f"PyTorch version: {torch.__version__}")
    if not torch.cuda.is_available():
        print("CUDA is unavailable; CPU training is supported.")
        print("For CUDA setup, follow docs/nnue-training.md and requirements.txt.")
        return 0
    for index in range(torch.cuda.device_count()):
        print(f"GPU {index}: {torch.cuda.get_device_name(index)}")
    try:
        device = torch.device("cuda")
        x = torch.rand(2048, 2048, device=device)
        y = torch.rand_like(x)
        torch.matmul(x, y)
        torch.cuda.synchronize(device)
        start = time.perf_counter()
        result = torch.matmul(x, y)
        torch.cuda.synchronize(device)
        elapsed = time.perf_counter() - start
        if not bool(torch.isfinite(result).all()):
            raise RuntimeError("GPU computation returned non-finite values")
        print(f"2048 x 2048 matrix multiplication: {elapsed:.6f} seconds (synchronized)")
        return 0
    except (RuntimeError, MemoryError) as error:
        print(f"GPU computation failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(check_gpu())
