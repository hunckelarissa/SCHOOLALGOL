| Lesson 4: loops (English syntax)
proc mainprogram
begin
  int sum
  sum := 0
  loop for i from 1 to 5
    sum := sum + i
  eloop
  output "sum 1..5 = ", sum
end
