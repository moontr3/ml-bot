from typing import *
import pygame as pg
import aiohttp
import aiofiles
from log import *
import time
import os
import utils
from PIL import Image


pg.display.init()
pg.font.init()


# pygame renderer

class Renderer:
    def __init__(self,
        size: Tuple[int, int] | None = None,
        fill: Tuple[int, int, int] | None = None,
        image: str | None = None
    ):
        '''
        A class that you can render images in.
        '''
        self.images: Dict[str, pg.Surface] = {}
        self.fonts: Dict[str, pg.font.Font] = {}
        self.init_time = time.time()
        self.cleanup: List[str] = []

        self.size: Tuple[int, int] = size
        self.surfaces: List[pg.Surface] = []
        self.new_image(fill, image)


    @property
    def surface(self) -> pg.Surface:
        return self.surfaces[-1]


    @surface.setter
    def surface(self, surface: pg.Surface):
        self.surfaces[-1] = surface
        self.size = surface.get_size()


    @property
    def frame(self) -> int:
        return len(self.surfaces)


    def new_image(self,
        fill: "Tuple[int, int, int] | None" = None,
        image: "str | None" = None
    ):
        if image:
            self.surfaces.append(self.get_image(image).copy())
            self.size = self.surfaces[-1].get_size()

        else:
            self.surfaces.append(pg.Surface(self.size, pg.SRCALPHA))
            if fill:
                self.surface.fill(fill)


    async def download_image(self, url:str) -> str:
        path = f'temp/{utils.rand_id()}.png'
        start_time = time.time()

        log(f'downloading image {url}', 'api')

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(path, mode='wb')
                    await f.write(await resp.read())
                    await f.close()

        log(f'image {path} downloaded in {time.time()-start_time}s', 'renderer')
        self.cleanup.append(path)
        return path


    def extend(self, size: int):
        new = pg.Surface((self.surface.get_width(), self.surface.get_height()+size), pg.SRCALPHA)
        new.blit(self.surface, (0,0))
        self.surface = new


    def get_image(self,
        path: str
    ):
        if path not in self.images:
            self.images[path] = pg.image.load(path)
        return self.images[path]


    def draw_image(self,
        path: str, pos: Tuple[int, int],
        size: Tuple[int, int] = None,
        h=0, v=0, area: pg.Rect=None,
        rotation: int = 0, opacity: int = 255,
        surface: pg.Surface = None
    ):
        image = self.get_image(path)

        if size:
            image = image.copy()
            image = pg.transform.smoothscale(image, size)

        if rotation != 0:
            image = pg.transform.rotate(image, rotation)

        if h != 0 or v != 0:
            pos = [
                pos[0]-image.get_width()*h,
                pos[1]-image.get_height()*v,
            ]

        image.set_alpha(opacity)

        if surface is None:
            surface = self.surface

        if area:
            surface.blit(image, pos, area)
        else:
            surface.blit(image, pos)


    def get_font(self,
        path: str, size: int
    ) -> pg.font.Font:
        if path+str(size) not in self.fonts:
            self.fonts[path+str(size)] = pg.font.Font(path, size)
        return self.fonts[path+str(size)]


    def draw_text(self,
        text: str, pos: Tuple[int, int], font:str, size:int,
        color:Tuple[int, int, int], h=0, v=0, rotation: int = 0,
        opacity: int = 255, max_size: int = None,
        surface: pg.Surface = None
    ) -> Tuple[int,int]:
        font: pg.font.Font = self.get_font(font, size)
        text: pg.Surface = font.render(text, True, color)

        if rotation != 0:
            text = pg.transform.rotate(text, rotation)

        if max_size and text.get_width() > max_size:
            text = pg.transform.smoothscale(text, (max_size, text.get_height()))

        if h != 0 or v != 0:
            pos = [
                pos[0]-text.get_width()*h,
                pos[1]-text.get_height()*v,
            ]

        if opacity != 255:
            text.set_alpha(opacity)

        if surface is None:
            surface = self.surface

        surface.blit(text, pos)
        return text.get_rect().size


    def render_text(self,
        text: str, font:str, size:int,
        color:Tuple[int, int, int], rotation: int = 0,
        opacity: int = 255, max_size: int = None
    ) -> pg.Surface:
        font: pg.font.Font = self.get_font(font, size)
        text: pg.Surface = font.render(text, True, color)

        if rotation != 0:
            text = pg.transform.rotate(text, rotation)

        if max_size and text.get_width() > max_size:
            text = pg.transform.smoothscale(text, (max_size, text.get_height()))

        if opacity != 255:
            text.set_alpha(opacity)

        return text


    def get_text_size(self,
        text: str, font:str, size:int
    ) -> Tuple[int,int]:
        font: pg.font.Font = self.get_font(font, size)
        return font.size(text)


    def round_image(self, surface: pg.Surface, radius: int) -> pg.Surface:
        '''
        Makes an image have rounded corners.
        '''
        rect = pg.Rect((0,0), surface.get_size())
        rect = rect.inflate(radius*2,radius*2)

        new = pg.Surface(surface.get_size(), pg.SRCALPHA)
        new.blit(surface, (0,0))
        pg.draw.rect(new, (0,0,0,0), rect, radius, radius*3)

        return new


    def save(self, dir:str, ext:str='jpg') -> str:
        '''
        ! This will only export the last added frame.
        '''
        start_time = time.time()
        filename = dir.rstrip('/\\')+'/' + utils.rand_id() + '.'+ext

        # saving
        pg.image.save(self.surface, filename)
        log(f'image {filename} saved in {time.time()-start_time}s', 'renderer')

        # cleaning up
        for i in self.cleanup:
            os.remove(i)
        self.cleanup = []

        log(f'image {filename} completed {time.time()-self.init_time}s', 'renderer')
        return filename


    def to_gif(self, dir:str, duration_ms:int) -> str:
        '''
        Exports all frames to a gif.
        '''
        start_time = time.time()
        filename = dir.rstrip('/\\')+'/' + utils.rand_id() + '.gif'

        # converting frames
        images = []

        for i in self.surfaces:
            b = pg.image.tobytes(i, "RGBA")
            images.append(Image.frombytes("RGBA", self.size, b))

        log(f'gif {filename} frames converted in {time.time()-start_time}s', 'renderer')

        # exporting
        try:
            im = next(iter(images))
            im.save(
                filename, save_all=True, append_images=images[1:],
                duration=duration_ms, disposal=2
            )
        except Exception as e:
            log(f'gif {filename} unable to export: {e}', level=ERROR)
            return

        log(f'gif {filename} exported {time.time()-self.init_time}s', 'renderer')

        # cleaning up
        for i in self.cleanup:
            os.remove(i)
        self.cleanup = []

        log(f'gif {filename} completed {time.time()-self.init_time}s', 'renderer')
        return filename
