| Lesson 9: record (rec) and fields
rec Point
begin
  real x, y
end

proc mainprogram
begin
  Point p
  p.x := 3.5
  p.y := 7
  output "x=", p.x, " y=", p.y
end
