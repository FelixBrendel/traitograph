import argparse

sample_usage = """example:

  python traitograph.py --names a b c --values 1 2 3 --max-value 4
  python traitograph.py -o "character.png" --names n1 n2 n3 n4 --values 1 3 2 3 --max-value 4
  python traitograph.py --names curious organized energetic friendly confident --values 5 4 3 4 2 --max-value 7 -d True
"""

parser = argparse.ArgumentParser(description="Generate a chart showing character traits.",
                                 epilog=sample_usage,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--out-file",       "-o", dest="out_file_name",
                    metavar="out_file", default="chart.png",
                    help="The file in which the image will be written. (Defaults to \"chart.png\")")
parser.add_argument("--names",          "-n", dest="names",
                    required=True, nargs="+", metavar="name",
                    help="The names of the character traits")
parser.add_argument("--values",         "-v", dest="values",
                    required=True, nargs="+", type=int, metavar="value",
                    help="The values for the character traits")
parser.add_argument("--max-value",      "-m", dest="max_value",
                    required=True, type=int, metavar="max",
                    help="The maximum value for any trait")
parser.add_argument("--foreground",    "-fg", dest="foreground",
                    nargs=3, type=int, default=[0,0,0], metavar="channel",
                    help="The foreground color of the chart. (Values from 0 to 255 -- defaults to [0,0,0])")
parser.add_argument("--backgournd",    "-bg", dest="background",
                    nargs=3, type=int, default=[255,255,255], metavar="channel",
                    help="The background color of the chart. (Values from 0 to 255 -- defaults to [255,255,255])")
parser.add_argument("--trait-color",   "-lc", dest="trait_color",
                    nargs=4, type=int, default=[0,190,190,100], metavar="channel",
                    help="The color of the colored part of the chart. (Values from 0 to 255 -- defaults to [0,190,190,100])")
parser.add_argument("--outer-padding", "-op", dest="outer_padding",
                    type=int, default=20, metavar="pixel_count",
                    help="The additional padding applied around the chart. (Defaults to 20)")
parser.add_argument("--line-spacing",  "-ls", dest="line_spacing",
                    type=int, default=40, metavar="pixel_count",
                    help="The additional padding applied around the chart. (Defaults to 40)")
parser.add_argument("--dot-size",      "-ds", dest="dot_size",
                    type=int, default=2, metavar="dot_size",
                    help="The size of the dots. (Defaults to 2)")
parser.add_argument("--display",        "-d", dest="display",
                    type=bool, default=False, metavar="display",
                    help="If True, shows the generated plot in a window. (Defaults to False)")
args = parser.parse_args()

import math
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame
from pygame import gfxdraw

# to have the first vertex at the top rather than the bottom, otherwise
# odd-numbered n-gons look like they are upside down
circle_offset = math.pi

def generate_n_gon_points(n, center, radii):
    alpha_step = math.tau / n

    if type(radii) == int:
        radii = [radii for i in range(n)]
    else:
        assert(len(radii) == n)

    # go clockwise, so flip the sign in the sin and cos, functions (I know
    # unnecessary for cos, but looks better when aligned :)
    return [(int(math.sin(-i * alpha_step + circle_offset) * radii[i] + center[0]), # x coordintate
             int(math.cos(-i * alpha_step + circle_offset) * radii[i] + center[1])) # y coordintate
            for i in range(n)]

def generate_plot_surface(dimension_count, values, max_value, line_spacing, foreground, background, trait_color, dot_size):
    # figure out exactly, how big the surface needs to be, by looking at the
    # outer most points
    radius = line_spacing * max_value
    points = generate_n_gon_points(dimension_count, (0,0), radius)

    max_x = max((point[0] for point in points))
    min_x = -max_x       # symmetry: fist point is always straight up
    min_y = -radius      # fist point is always straight up
    max_y = max((point[1] for point in points))

    padding = dot_size//2 + 4
    surface_size = (max_x - min_x + 2*(padding),
                    max_y - min_y + 2*(padding))

    plot_center = [surface_size[0] // 2,
                   radius + padding]

    # generate the surface
    surface = pygame.Surface(surface_size)
    surface.fill(background)

    transparent_overlay = pygame.Surface(surface_size, pygame.SRCALPHA)
    transparent_overlay.set_alpha(100) #TODO(Felix): make this adjustable

    font = pygame.font.Font(pygame.font.get_default_font(), int(line_spacing*0.4))
    for i in range(max_value):
        points = generate_n_gon_points(dimension_count, plot_center, radius)
        
        pygame.draw.aalines(surface, foreground, True, points)

        for point in points:
            gfxdraw.filled_circle(surface, point[0], point[1], dot_size, foreground)
            gfxdraw.aacircle(surface, point[0], point[1], dot_size, foreground)

        textsurface = font.render(f"{max_value-i}", True, foreground)

        text_location = (points[0][0] - textsurface.get_size()[0] // 2,
                         points[0][1] + int(line_spacing * 0.2))
        surface.blit(textsurface,text_location)

        radius -= line_spacing

    # draw in the trait polygon
    radii = [value * line_spacing for value in values]
    trait_points = generate_n_gon_points(dimension_count, plot_center, radii)
    print(trait_points)

    trait_color_full_alpha = trait_color[:3]
    for point in trait_points:
        gfxdraw.filled_circle(surface, point[0], point[1], 4, trait_color_full_alpha)
    
    pygame.draw.aalines(surface, trait_color_full_alpha, True, trait_points)

    # draw the transparent polygon
    pygame.draw.polygon(transparent_overlay, trait_color, trait_points)
    surface.blit(transparent_overlay, (0,0))
    
    return surface


def plot(names, values, max_value, foreground, background, trait_color, out_file_name, display, outer_padding, line_spacing, dot_size):
    number_dimensions = len(names)
    assert(number_dimensions == len(values))
    assert(max_value > 0)

    pygame.init()

    plot_surface = generate_plot_surface(number_dimensions, values, max_value, line_spacing, foreground, background, trait_color, dot_size)

    final_surface = plot_surface
    pygame.image.save(final_surface, out_file_name)

    if display:
        window = pygame.display.set_mode(final_surface.get_size())
        pygame.display.set_caption("Traitograph")
        window.blit(final_surface, (0,0))
        pygame.display.update()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
    else:
        print("done")
    pygame.quit()

plot(**vars(args))
