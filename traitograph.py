import argparse

sample_usage = """example:

  python traitograph.py --labels a b c --values 1 2 3 --max-value 4
  python traitograph.py -o "character.png" --labels n1 n2 n3 n4 --values 1 3 2 3 --max-value 4
  python traitograph.py --labels curious organized energetic friendly confident --values 5 4 3 4 2 --max-value 7 -d True
"""

parser = argparse.ArgumentParser(description="Generate a chart showing character traits.",
                                 epilog=sample_usage,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument("--labels",         "-l", dest="labels",
                    required=True, nargs="+", metavar="label",
                    help="The names of the character traits")
parser.add_argument("--values",         "-v", dest="values",
                    required=True, nargs="+", type=int, metavar="value",
                    help="The values for the character traits")
parser.add_argument("--max-value",      "-m", dest="max_value",
                    required=True, type=int, metavar="max",
                    help="The maximum value for any trait")
parser.add_argument("--out-file",       "-o", dest="out_file_name",
                    metavar="out_file", default="chart.png",
                    help="The file to which the image will be written. (Defaults to \"chart.png\")")
parser.add_argument("--foreground",    "-fg", dest="foreground",
                    nargs=3, type=int, default=[0,0,0], metavar="channel",
                    help="The foreground color of the chart. (Values from 0 to 255 -- defaults to [0,0,0])")
parser.add_argument("--background",    "-bg", dest="background",
                    nargs=3, type=int, default=[255,255,255], metavar="channel",
                    help="The background color of the chart. (Values from 0 to 255 -- defaults to [255,255,255])")
parser.add_argument("--trait-color",   "-tc", dest="trait_color",
                    nargs=4, type=int, default=[0,190,190,100], metavar="channel",
                    help="The color of the colored part of the chart. (Values from 0 to 255 -- defaults to [0,190,190,100])")
parser.add_argument("--outer-padding", "-op", dest="outer_padding",
                    type=int, default=20, metavar="pixel_count",
                    help="The additional padding applied around the chart. (Defaults to 20)")
parser.add_argument("--line-spacing",  "-ls", dest="line_spacing",
                    type=int, default=40, metavar="pixel_count",
                    help="The distance between the lines. (Defaults to 40)")
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


def generate_angles(n):
    return [i * math.tau / n for i in range(n)]


def generate_n_gon_points(n, center, radii):
    if type(radii) == int:
        radii = [radii] * n
    else:
        assert(len(radii) == n)

    # to have the first vertex at the top rather than the bottom, otherwise
    # odd-numbered n-gons look like they are upside down:
    circle_offset = math.pi

    # go clockwise, so flip the sign in the sin and cos, functions (I know it's
    # unnecessary for cos, but it looks better when aligned :)
    return [(int(math.sin(-angle + circle_offset) * radius + center[0]),  # x coordintate
             int(math.cos(-angle + circle_offset) * radius + center[1]))  # y coordintate
            for angle, radius in zip(generate_angles(n), radii)]


def draw_trait_polygon(surface, plot_center):
    transparent_overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    radii = [value * args.line_spacing for value in args.values]
    trait_points = generate_n_gon_points(len(radii), plot_center, radii)

    trait_color_full_alpha = args.trait_color[:3]
    for point in trait_points:
        gfxdraw.filled_circle(surface, point[0], point[1], args.dot_size, trait_color_full_alpha)
        gfxdraw.aacircle(surface, point[0], point[1], args.dot_size, trait_color_full_alpha)

    pygame.draw.aalines(surface, trait_color_full_alpha, True, trait_points)
    # draw the transparent polygon
    pygame.draw.polygon(transparent_overlay, args.trait_color, trait_points)
    surface.blit(transparent_overlay, (0,0))


def generate_labels(points, surface):
    label_surfaces = [font.render(label, True, args.foreground) for label in args.labels]
    label_offsets = []

    tolerance = 0.05

    min_x = 0
    min_y = 0
    max_x, max_y = surface.get_size()

    # calcualte the offsets for all the labels, depeneding on the position
    # around the plot
    for label_surface, point, alpha in zip(label_surfaces, points, generate_angles(len(points))):
        label_width, label_height = label_surface.get_size()

        # these offsets are for offsetting the actual label, so that it has soem
        # distance form the point it is supposed to stick to
        vertical_text_offset = 5
        horizontal_text_offset = 10

        if abs(alpha) < tolerance: # label is at top
            offset = (-label_width//2, -label_height - vertical_text_offset)
        elif abs(alpha-math.pi) < tolerance: # label is at bottom
            offset = (-label_width//2, + vertical_text_offset)
        elif abs(alpha-math.tau/4) < tolerance: # label is at right
            offset = (horizontal_text_offset, -label_height//2)
        elif abs(alpha-3*math.tau/4) < tolerance: # label is at left
            offset = (-label_width-horizontal_text_offset, -label_height//2)
        elif 0 < alpha < math.tau/4: # label is at top right
            offset = (horizontal_text_offset//2, -label_height-vertical_text_offset//2)
        elif math.tau/4 < alpha < math.tau/2: # label is at bottom right
            offset = (horizontal_text_offset//2, vertical_text_offset//2)
        elif math.tau/2 < alpha < 3*math.tau/4: # label is at bottom left
            offset = (-label_width-horizontal_text_offset//2, vertical_text_offset//2)
        else: # label is at top left
            offset = (-label_width-horizontal_text_offset//2, -label_height-vertical_text_offset//2)

        min_x = min(min_x, point[0] + offset[0])
        max_x = max(max_x, point[0] + offset[0] + label_width)

        min_y = min(min_y, point[1] + offset[1])
        max_y = max(max_y, point[1] + offset[1] + label_height)

        label_offsets.append(offset)

    # calculate new surface size
    padding = 10
    width = max_x - min_x + 2*padding
    height = max_y - min_y + 2*padding

    new_surface = pygame.Surface((width, height))
    new_surface.fill(args.background)

    # blit the original plot
    new_surface.blit(surface, (-min_x + padding,-min_y + padding))

    # blit all the labels
    for label_offset, label_surface, point in zip(label_offsets, label_surfaces, points):
        new_surface.blit(label_surface, (point[0] + label_offset[0] - min_x + padding, point[1] + label_offset[1] -min_y + padding))
    return new_surface


def generate_plot():
    # figure out exactly, how big the surface needs to be, by looking at the
    # outer most points
    dimension_count = len(args.labels)
    radius = args.line_spacing * args.max_value
    points = generate_n_gon_points(dimension_count, (0, 0), radius)

    max_x = max((point[0] for point in points))
    min_x = -max_x       # symmetry: fist point is always straight up
    min_y = -radius      # fist point is always straight up
    max_y = max((point[1] for point in points))

    padding = args.dot_size//2 + 4
    surface_size = (max_x - min_x + 2*(padding),
                    max_y - min_y + 2*(padding))

    plot_center = [surface_size[0] // 2,
                   radius + padding]

    # generate the surface
    surface = pygame.Surface(surface_size)
    surface.fill(args.background)

    radius = args.line_spacing
    for i in range(args.max_value):
        points = generate_n_gon_points(dimension_count, plot_center, radius)

        pygame.draw.aalines(surface, args.foreground, True, points)

        for point in points:
            gfxdraw.filled_circle(surface, point[0], point[1], args.dot_size, args.foreground)
            gfxdraw.aacircle(surface, point[0], point[1], args.dot_size, args.foreground)

        textsurface = font.render(f"{i+1}", True, args.foreground)

        text_location = (points[0][0] - textsurface.get_size()[0] // 2,
                         points[0][1] + int(args.line_spacing * 0.2))
        surface.blit(textsurface, text_location)

        radius += args.line_spacing

    # draw in the trait polygon
    draw_trait_polygon(surface, plot_center)

    # generate the labels
    return generate_labels(points, surface)


if __name__ == "__main__":
    assert(len(args.labels) == len(args.values))
    assert(args.max_value > 0)

    pygame.init()
    font = pygame.font.Font(pygame.font.get_default_font(), int(args.line_spacing*0.4))

    surface = generate_plot()

    pygame.image.save(surface, args.out_file_name)

    if args.display:
        window = pygame.display.set_mode(surface.get_size())
        pygame.display.set_caption("Trait-o-graph")
        window.blit(surface, (0, 0))

        pygame.display.update()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
    else:
        print("done")

    pygame.quit()
