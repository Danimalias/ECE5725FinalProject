#genMatr.py Below
#!/usr/bin/env python
import argparse
import math
import sys
from PIL import Image
def spherical_deform(img, out_height=None):
# Idea here: We map rows from the source image onto rows in the destination
# image so that the visual depiction of the image on a spherical display
# will appear to be the same as if the display were planar.
#
# For a spherical display of 36 pixels in height, the real-world y-value
# of the pixel location is sin(theta) where theta is the latitude of the
# pixel. North pole has y-value of 1, equator of 0, and south pole of -1.
#
# For each row in the source image, we want to determine which pixel
# (== which angle theta) it should map onto in the destination image. The
# destination image is always 36 pixels high.
#
# For a source image y-value of y_s, the corresponding pixel latitude
# is theta = arcsin(y_s). For y_s = 1, theta = pi/2 or 90 degrees.
# For y_s = 0, theta = 0, and y_s = -1, theta = -pi/2.
#
# Therefore, we map each row of the source image onto the range (1, -1)
# where y_s = 1 is the top row, and y_s = -1 is the bottom row. We then
# calculate theta = arcsin(y_s) for each row of the source image, as above.
# We then calculate the corresponding pixel position as pixel_num = theta / 36
# (where theta ranges from pi/2 to -pi/2).
#
# Because a typical source image will have many more rows than we have pixels,
# we can perform resampling to assign a final color to each pixel.
(in_width, in_height) = img.size
out_height = out_height or in_height
out_width = (in_width / in_height) * out_height
# We start by scaling only in the y-dimension, then we scale in the x.
out_img = Image.new("RGB", (in_width, out_height))
in_pixels = img.load()
out_pixels = out_img.load()
# Map from 0 .. in_height -> 1 .. -1
slope = -2.0 / in_height
offset = 1.0
last_out_row = 0
for in_row in range(in_height):
in_row_scaled = slope * in_row + offset
theta = math.asin(in_row_scaled)
# pixel_num = (theta / out_height)
# Map from pi/2 .. -pi/2 -> 0 .. out_height
m = out_height / -math.pi
b = out_height / 2
target_row = math.floor((m * theta) + b)
if in_row == in_height - 1:
target_row = out_height - 1
# print(f"Row {in_row} -> {target_row}")
for out_row in range(last_out_row, target_row + 1):
for x in range(in_width):
out_pixels[x, out_row] = in_pixels[x, in_row]
last_out_row = target_row
return out_img
def process_image(
infile, outfile, name, width, height, outimage=False, spherical=False
):
img = Image.open(infile)
img = img.convert("RGB")
if spherical:
img = spherical_deform(img)
img = img.resize((width, height), resample=Image.NEAREST)
if outimage:
img.save(outfile)
print(f"Saved scaled image to {outfile}")
return
pixels = list(img.getdata())
with open(outfile, "w+") as outf:
outf.write(
f"// Generated by genheader.py --name {name} --width {width} "
f"--height {height} {infile} {outfile}\n"
)
outf.write(f"#define IMAGE_COLUMNS_{name} {width}\n")
outf.write(f"#define IMAGE_ROWS_{name} {height}\n")
outf.write(f"const static uint8_t IMAGE_{name}[] = {{\n")
for pixel in pixels:
r, g, b = pixel
outf.write(f"{b:#04x}, {g:#04x}, {r:#04x},\n")
outf.write("};\n")
print(f"Saved header to {outfile}")
def main():
parser = argparse.ArgumentParser()
parser.add_argument("--name", type=str, required=True)
parser.add_argument("--width", type=int, default=72)
parser.add_argument("--height", type=int, default=36)
parser.add_argument(
"--outimage",
action="store_true",
help="Write output as image, rather than header",
)
parser.add_argument(
"--spherical",
action="store_true",
help="Stretch image vertically to compensate for spherical projecton",
)
parser.add_argument("infile")
parser.add_argument("outfile")
args = parser.parse_args()
process_image(
args.infile,
args.outfile,
args.name,
args.width,
args.height,
args.outimage,
args.spherical,
)
if __name__ == "__main__":
main()