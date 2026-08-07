| Lesson 8: reading system hosts file (full FS access)
| WARNING: uses absolute OS path. Change path for your system. Educational use only.
proc mainprogram
begin
  file f
  str path
  str line
  int n
  path := "C:\\Windows\\System32\\drivers\\etc\\hosts"
  open(f, path, "read")
  n := 0
  loop while (not eof(f)) and (n < 5)
    input f, line
    n := n + 1
    output n, ": ", line
  eloop
  close(f)
  output "lines read: ", n
end
