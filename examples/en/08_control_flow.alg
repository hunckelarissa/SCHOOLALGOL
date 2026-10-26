| Lesson 8: step, break, continue, return
proc Sign(arg int x; res int s)
begin
  if x > 0 then
    return 1
  endif
  if x < 0 then
    return -1
  endif
  s := 0
end

proc mainprogram
begin
  int i, sum
  sum := 0
  | step 2: 1 3 5
  loop for i from 1 to 5 step 2
    sum := sum + i
  eloop
  output "sum step2 = ", sum

  | skip 3 via continue → 1 2 4 5
  loop for i from 1 to 5
    if i = 3 then
      continue
    endif
    output i
  eloop

  | break at 4
  loop for i from 1 to 10
    if i = 4 then
      break
    endif
    output "until ", i
  eloop

  | nested loops: break/continue affect the nearest loop only
  loop for i from 1 to 2
    loop for j from 1 to 5
      if j = 3 then
        break
      endif
      output i, "*", j
    eloop
  eloop

  output "sign ", Sign(-7)
end
