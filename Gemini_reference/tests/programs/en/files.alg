proc mainprogram
begin
  file f
  str msg
  msg := "file_ok"
  open(f, "out.txt", "write")
  output f, msg
  close(f)
  open(f, "out.txt", "read")
  input f, msg
  close(f)
  output msg
end
