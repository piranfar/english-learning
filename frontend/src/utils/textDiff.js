/**
 * Simple word-level diff for learner vs AI text comparison.
 * TODO: Advanced Microsoft Word-style track changes (accept/reject, inline bubbles).
 */

function tokenize(text) {
  return (text || '').split(/(\s+)/).filter((part) => part.length > 0)
}

export function diffWords(leftText, rightText) {
  const left = tokenize(leftText)
  const right = tokenize(rightText)
  const m = left.length
  const n = right.length
  const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0))

  for (let i = 1; i <= m; i += 1) {
    for (let j = 1; j <= n; j += 1) {
      if (left[i - 1] === right[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1])
      }
    }
  }

  const leftParts = []
  const rightParts = []
  let i = m
  let j = n

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && left[i - 1] === right[j - 1]) {
      leftParts.unshift({ type: 'same', text: left[i - 1] })
      rightParts.unshift({ type: 'same', text: right[j - 1] })
      i -= 1
      j -= 1
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      rightParts.unshift({ type: 'add', text: right[j - 1] })
      leftParts.unshift({ type: 'pad', text: '' })
      j -= 1
    } else {
      leftParts.unshift({ type: 'remove', text: left[i - 1] })
      rightParts.unshift({ type: 'pad', text: '' })
      i -= 1
    }
  }

  return { leftParts, rightParts }
}

export function hasDiff(leftText, rightText) {
  return (leftText || '').trim() !== (rightText || '').trim()
}
