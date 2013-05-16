'''
TODO: ideally, it would be nice to be able to reuse the FBO texture, or bind the
current created texture into the FBO. But i got INCOMPLETE ATTACHEMENT error in
GL. My guess (after checking apitrace) is that the created texture is not really
filled by the texture, yet. And if we try to fill it, the texture is created
with a callback, so it's not gonna to work either.

So right now, we use fbo.pixels, it sucks a lot, but working.
'''

import ast
from os.path import join, dirname
from kivy.app import App
from kivy.uix.label import Label
from kivy.core.image import ImageData
from kivy.core.text import LabelBase
from kivy.graphics.fbo import Fbo
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.lang import Builder


class BMFont(object):

    def __init__(self, filename):
        super(BMFont, self).__init__()
        self.basedir = dirname(filename)
        self.pages = {}
        self.texpages = {}
        self.texchars = {}
        self.chars = {}
        with open(filename) as fd:
            for line in fd.readlines():
                tokens = self._parse_line(line)
                cmd, data = tokens
                if not cmd:
                    continue

                if cmd == 'info':
                    self.info = data
                elif cmd == 'common':
                    self.common = data
                elif cmd == 'page':
                    self.pages[data['id']] = data
                    self._load_page(data['id'])
                elif cmd == 'chars':
                    pass
                elif cmd == 'char':
                    self.chars[int(data['id'])] = data

    def _parse_line(self, line):
        # FIXME split on the space is not enought, some token have string with
        # "...", and it can contain spaces too.
        line = line.splitlines()[0]
        if not line:
            return None, None

        data = {}
        tokens = []
        for part in line.split('='):
            tokens.extend(part.rsplit(' ', 1))
        cmd, tokens = tokens[0], tokens[1:]

        for k, v in zip(tokens[::2], tokens[1::2]):
            data[k] = ast.literal_eval(v)

        return cmd, data

    def _load_page(self, uid):
        filename = self.pages[uid]['file']
        self.texpages[uid] = CoreImage(join(self.basedir, filename)).texture

    def get_extents(self, c):
        oc = ord(c)
        if oc not in self.chars:
            return 0, 0
        ic = self.chars[oc]
        w = ic['xadvance']
        h = ic['height'] + ic['yoffset']
        return w, h

    def get_texture_char(self, c):
        oc = ord(c)
        ic = self.chars[oc]
        region = self.texpages[ic['page']].get_region(
            ic['x'], self.common['scaleH'] - ic['y'],
            ic['width'], -ic['height'])
        return region

    def get_info_char(self, c):
        return self.chars.get(ord(c))


class BMCoreLabel(LabelBase):

    _cache = {}

    def _select_font(self):
        source = self.options['font_name']
        if not source:
            raise Exception('BMLabel: source is missing')
        font = BMCoreLabel._cache.get(source)
        if not font:
            font = BMFont(source)
            BMCoreLabel._cache[source] = font
        return font

    def get_extents(self, text):
        font = self._select_font()
        w = 0
        for c in text:
            cw, ch = font.get_extents(c)
            w += cw
        return w, font.common['lineHeight']

    def _render_begin(self):
        self._font = self._select_font()
        self.texture = self.texture
        self.texture.bind()
        self._fbo = Fbo(size=self._size)
        with self._fbo:
            Color(1, 1, 1)

    def _render_text(self, text, x, y):
        with self._fbo:
            for c in text:
                x += self._render_glyph(c, x, y)

    def _render_end(self):
        fbo = self._fbo
        fbo.draw()
        return ImageData(fbo.size[0], fbo.size[1], 'rgba', fbo.pixels)

    def _render_glyph(self, c, x, y):
        ic = self._font.get_info_char(c)
        if not ic:
            return 0
        texture = self._font.get_texture_char(c)
        h = ic['height']
        Rectangle(
            pos=(x + ic['xoffset'], y + ic['yoffset']),
            size=(ic['width'], h),
            texture=texture)
        return ic['xadvance']


class BMLabel(Label):

    def _create_label(self):
        d = Label._font_properties
        dkw = dict(zip(d, [getattr(self, x) for x in d]))
        self._label = BMCoreLabel(**dkw)


class BMTestApp(App):
    title = 'BM Font tester'
    def build(self):
        return Builder.load_string('''
GridLayout:
    cols: 1

    GridLayout:
        rows: 1
        spacing: '10sp'
        height: '44sp'
        size_hint_y: None

        Button:
            text: 'geneva'
            on_release: bm.font_name = 'fonts/{}.fnt'.format(self.text)
        Button:
            text: 'handel'
            on_release: bm.font_name = 'fonts/{}.fnt'.format(self.text)
        Button:
            text: 'handelg'
            on_release: bm.font_name = 'fonts/{}.fnt'.format(self.text)
        Button:
            text: 'hiero'
            on_release: bm.font_name = 'fonts/{}.fnt'.format(self.text)
        Button:
            text: 'lucida'
            on_release: bm.font_name = 'fonts/{}.fnt'.format(self.text)
        Button:
            text: 'snap1'
            on_release: bm.font_name = 'fonts/{}.fnt'.format(self.text)
        Button:
            text: 'snap'
            on_release: bm.font_name = 'fonts/{}.fnt'.format(self.text)
        Button:
            text: 'test'
            on_release: bm.font_name = 'fonts/{}.fnt'.format(self.text)
        Button:
            text: 'times'
            on_release: bm.font_name = 'fonts/{}.fnt'.format(self.text)

    GridLayout:
        cols: 2
        spacing: '25sp'
        padding: '25sp'

        TextInput:
            id: ti
            text: 'Hello world'

        BMLabel:
            id: bm
            font_name: 'fonts/geneva.fnt'
            text: ti.text
            text_size: self.width, None
''')

BMTestApp().run()
