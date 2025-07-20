# Fibonacci Workflow Example

This example demonstrates a multi-step workflow where the AI:
1. Shows Fibonacci in Scheme
2. Creates a TLA+ formal specification
3. Reviews and suggests improvements

## Expected Interaction

```bash
$ python -m gemini_repl

╔══════════════════════════════════════╗
║      🌟 Gemini REPL v0.1.0 🌟        ║
║  Python-powered AI conversations     ║
║  Type /help for available commands   ║
╚══════════════════════════════════════╝

Session ID: abc123...

[0 tokens] > show fibonacci in scheme

Here's the Fibonacci function in Scheme with both recursive and iterative versions:

```scheme
;; Classic recursive implementation
(define (fibonacci n)
  (cond
    ((= n 0) 0)
    ((= n 1) 1)
    (else (+ (fibonacci (- n 1))
             (fibonacci (- n 2))))))

;; Tail-recursive version (more efficient)
(define (fib-tail n)
  (define (fib-iter n a b)
    (if (= n 0)
        a
        (fib-iter (- n 1) b (+ a b))))
  (fib-iter n 0 1))

;; Example usage:
;; (fibonacci 10) => 55
;; (fib-tail 10) => 55
```

The recursive version is elegant but has exponential time complexity. The tail-recursive version is O(n) and won't cause stack overflow for large n.

[150 tokens] > create a TLA+ spec for that and add it to research/formal/

🔧 Using tool: write_file
✍️  Writing: research/formal/Fibonacci.tla

I've created a TLA+ specification for the Fibonacci sequence at `research/formal/Fibonacci.tla`. The specification includes:

1. **Recursive definition** matching the Scheme implementation
2. **Iterative computation** for efficient model checking
3. **Property verification** to ensure correctness
4. **Invariants** about the sequence properties

The TLA+ spec can be model-checked to verify properties like:
- Correctness of the computation
- Monotonicity of the sequence
- Relationship between consecutive terms

[280 tokens] > show research/formal/Fibonacci.tla and suggest improvements

🔧 Executing tool: read_file
📄 Reading: research/formal/Fibonacci.tla

```tla
---- MODULE Fibonacci ----
EXTENDS Naturals, Sequences

(* Recursive definition of Fibonacci *)
RECURSIVE Fib(_)
Fib(n) == 
  IF n = 0 THEN 0
  ELSE IF n = 1 THEN 1
  ELSE Fib(n-1) + Fib(n-2)

(* Iterative computation for model checking *)
FibSeq(n) == 
  LET RECURSIVE FibIter(_, _, _)
      FibIter(k, a, b) == 
        IF k = 0 THEN a
        ELSE FibIter(k-1, b, a+b)
  IN FibIter(n, 0, 1)

(* Property: Fibonacci sequence is strictly increasing after n=1 *)
FibIncreasing == 
  \A n \in Nat : n > 1 => Fib(n) > Fib(n-1)

====
```

## Suggested Improvements:

### 1. Add Bounded Model Checking
```tla
CONSTANT MaxN  \* Set in model to limit state space
ASSUME MaxN \in Nat /\ MaxN > 0

FibDomain == 0..MaxN
```

### 2. Add Golden Ratio Property
```tla
(* Property: Ratio converges to golden ratio *)
GoldenRatio == 1.618033988749895  \* Approximation

FibRatioConverges == 
  \A n \in Nat : n > 10 => 
    LET ratio == Fib(n+1) / Fib(n)
    IN ABS(ratio - GoldenRatio) < 0.01
```

### 3. Add Sequence Generation
```tla
(* Generate first N Fibonacci numbers *)
FibSequence(n) == 
  [i \in 0..n |-> Fib(i)]

(* Property: Sum of first n Fibonacci numbers *)
FibSum(n) == 
  LET seq == FibSequence(n)
  IN FoldSeq(LAMBDA a,b: a+b, 0, seq)

FibSumProperty == 
  \A n \in FibDomain : FibSum(n) = Fib(n+2) - 1
```

### 4. Add Matrix Form
```tla
(* Matrix multiplication approach *)
FibMatrix == <<
  <<1, 1>>,
  <<1, 0>>
>>

MatrixPower(M, n) == 
  IF n = 0 THEN <<<<1,0>>, <<0,1>>>>  \* Identity
  ELSE IF n = 1 THEN M
  ELSE (* Fast exponentiation *)
    LET half == MatrixPower(M, n \div 2)
        squared == MatrixMultiply(half, half)
    IN IF n % 2 = 0 THEN squared
       ELSE MatrixMultiply(squared, M)
```

### 5. Add Temporal Properties
```tla
(* For checking liveness in a generating system *)
GenerateNext == 
  /\ n' = n + 1
  /\ fib_n' = fib_n + fib_n_minus_1
  /\ fib_n_minus_1' = fib_n

EventuallyGeneratesAll == 
  \A k \in Nat : <>(fib_n = Fib(k))
```

These improvements would make the specification more complete for:
- Bounded model checking (practical verification)
- Mathematical property verification
- Alternative computation methods
- Temporal reasoning about Fibonacci generation

[650 tokens] >
```

## Key Points

1. **Immediate Action**: The AI doesn't ask "would you like me to show you Fibonacci?" - it just shows it
2. **Directory Creation**: When asked to put the file in `research/formal/`, the directory is created automatically
3. **Tool Chaining**: The AI reads the file immediately when asked to review it
4. **No Advisory Language**: No "you should" or "you can" - just direct action

## Testing This Workflow

To test this workflow:

```bash
# 1. Start the REPL
python -m gemini_repl

# 2. Type these commands in sequence:
show fibonacci in scheme
create a TLA+ spec for that and add it to research/formal/
show research/formal/Fibonacci.tla and suggest improvements

# 3. Verify:
- Scheme code is shown immediately
- Directory research/formal/ is created
- File Fibonacci.tla is written
- File is read and improvements suggested
```

## Security Notes

The `write_file` function:
- ✅ Creates parent directories if needed
- ✅ Only within the project sandbox
- ❌ Rejects paths with `..`
- ❌ Rejects absolute paths
- ❌ Rejects symlinks

Safe examples:
- `research/formal/Spec.tla` ✅
- `docs/rfcs/2024/proposal.md` ✅
- `experiments/tla/model/Check.cfg` ✅

Rejected examples:
- `../../../etc/passwd` ❌
- `/tmp/evil.sh` ❌
- `safe/../../../etc/passwd` ❌
