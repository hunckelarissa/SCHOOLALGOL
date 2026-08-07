| Lesson 6: files — path passed to OS without restrictions
proc mainprogram
begin
  file f
  str text
  text := "line to file"
  open(f, "notes.txt", "write")
  output f, text
  close(f)
  open(f, "notes.txt", "read")
  input f, text
  close(f)
  output "from file: ", text
end
