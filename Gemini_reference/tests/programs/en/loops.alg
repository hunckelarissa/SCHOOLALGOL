proc mainprogram
begin
  int i
  int s
  s := 0
  loop for i from 1 to 5
    s := s + i
  eloop
  output "sum:", s
  loop while i > 0
    i := i - 1
  eloop
  output "i:", i
end
