import os
import subprocess


VERTICAL, HORIZONTAL = 'v', 'h'

def execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = popen.communicate("")
    if stderr:
        raise Exception("error: %s" % stderr)
    return stdout

class SpriteImage(object):
    def __init__(self, path, name=None):
        self.path = path
        self.name = name or os.path.splitext(os.path.basename(path))[0]
    
    @property
    def size(self):
        if not hasattr(self, '_size'):
            from PIL import Image
            img = Image.open(self.path)
            self._size = img.size
        return self._size


class Sprite(object):
    def __init__(self, sources=(), offsets=(0, 0), align=VERTICAL, name=None):
        self.images = [SpriteImage(source) for source in sources]
        self.offsets = offsets
        self.align = align
        self.name = name
        
    @property
    def relpath(self):
        return "icons/%s.png" % self.name
    
    def generate_scss(self, f, name=None):
        name = name or self.name
        f.write(".%s{background-image: url(%s);}\n\n" % (name, self.relpath))
        offset = 0
        shortcut_mixin = []
        for image in self.images:
            x, y = -self.offsets[0], -offset
            f.write("@mixin %s-%s($dx : 0px, $dy : 0px){@extend .%s;background-position: %spx + $dx %spx + $dy;}\n" % (name, image.name, name, x, y))
            shortcut_mixin.append("&.%s{@include %s-%s($dx, $dy);}" % (image.name, name, image.name))
            offset += image.size[1] + self.offsets[1]
        f.write("\n@mixin %s($dx : 0px, $dy : 0px){\n    %s\n}\n" % (name, "\n    ".join(shortcut_mixin)))
        
    def generate_image(self, f):
        w, h = 0, 0
        for image in self.images:
            w = max(image.size[0], w)
            h = max(image.size[1], h)
        cmd = ['montage', 
            '-background', 'transparent', 
            '-tile', '1x%s' % len(self.images),
            '-gravity', 'NorthWest', 
            '-geometry', '%sx%s' % (w + self.offsets[0], h + self.offsets[1]),
        ]
        cmd += [image.path for image in self.images]
        cmd.append('-')
        f.write(execute(cmd))
