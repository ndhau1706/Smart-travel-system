function hashCode(seed: string): number {
  let h = 0;
  for (let i = 0; i < seed.length; i += 1) {
    h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  }
  return h >>> 0;
}

export function createVoucherCode(seed: string): string {
  const hash = hashCode(seed);
  const code = hash % 10_000_000_000;
  return String(code).padStart(10, "0");
}

function drawFinder(matrix: boolean[][], row: number, col: number) {
  for (let r = 0; r < 7; r += 1) {
    for (let c = 0; c < 7; c += 1) {
      const border = r === 0 || r === 6 || c === 0 || c === 6;
      const inner = r >= 2 && r <= 4 && c >= 2 && c <= 4;
      matrix[row + r][col + c] = border || inner;
    }
  }
}

function isInFinder(row: number, col: number, size: number): boolean {
  const topLeft = row < 7 && col < 7;
  const topRight = row < 7 && col >= size - 7;
  const bottomLeft = row >= size - 7 && col < 7;
  return topLeft || topRight || bottomLeft;
}

export function buildVoucherMatrix(code: string, size = 21): boolean[][] {
  const matrix = Array.from({ length: size }, () => Array.from({ length: size }, () => false));
  drawFinder(matrix, 0, 0);
  drawFinder(matrix, 0, size - 7);
  drawFinder(matrix, size - 7, 0);

  let seed = hashCode(code);
  for (let r = 0; r < size; r += 1) {
    for (let c = 0; c < size; c += 1) {
      if (isInFinder(r, c, size)) continue;
      seed = (seed * 1664525 + 1013904223) >>> 0;
      matrix[r][c] = (seed & 1) === 0;
    }
  }
  return matrix;
}
