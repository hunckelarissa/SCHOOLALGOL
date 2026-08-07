rec Point
begin
  real x
  real y
end

proc mainprogram
begin
  Point p
  p.x := 3.0
  p.y := 4.0
  output p.x:6:1, p.y:6:1
end
