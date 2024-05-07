import cv2, asyncio, aiohttp
import numpy as np
from PIL import Image
from io import BytesIO

class Location:
    def __init__(self, data: dict) -> None:
        self.latitude = data.get("lat")
        self.longitude = data.get("lng")
        self.pano_id = data.get("panoId")
        self.heading = data.get("heading", 0)
        self.pitch = data.get("pitch", 0)
        self.country_code = data.get("countryCode", "us")
        self.country_name = data.get("countryName", "United States")
        self.dl_workers = 80
        self.semaphore = asyncio.BoundedSemaphore(self.dl_workers)
        self.zoom = 3
        self.max_tiles_x = 2 ** self.zoom
        self.max_tiles_y = 2 ** (self.zoom - 1)
        self.tile_size = 512
        self.alt_tile_size = 416
        self.fov = 110
        self.output_width = 1920 / 2
        self.output_height = 1080 / 2

    async def download_tile(self, x, y):
        url = f"https://cbk0.google.com/cbk?output=tile&panoid={self.pano_id}&x={x}&y={y}&zoom={self.zoom}"
        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    image_content = await response.read()
                    return Image.open(BytesIO(image_content))

    async def download(self):
        image = Image.new("RGB", (self.tile_size * self.max_tiles_x, self.tile_size * self.max_tiles_y))
        tasks = []
        for x in range(self.max_tiles_x):
            for y in range(self.max_tiles_y):
                tasks.append(self.download_tile(x, y))
        downloaded_tiles = await asyncio.gather(*tasks)
        for (x, y), tile in zip([(x, y) for x in range(self.max_tiles_x) for y in range(self.max_tiles_y)], downloaded_tiles):
            if tile:
                image.paste(tile, (x * self.tile_size, y * self.tile_size))
                tile.close()
        return self.project(self.crop_borders(image))

    def project(self, image: Image.Image) -> Image.Image:
        img = cv2.cvtColor(np.array(image.convert(mode="RGB")), cv2.COLOR_RGB2BGR)
        f = 0.5 * self.output_width * 1 / np.tan(0.5 * self.fov / 180.0 * np.pi)
        cx = (self.output_width - 1) / 2.0
        cy = (self.output_height - 1) / 2.0
        k = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1]], np.float32)
        k_inv = np.linalg.inv(k)
        x = np.arange(self.output_width)
        y = np.arange(self.output_height)
        x, y = np.meshgrid(x, y)
        z = np.ones_like(x)
        xyz = np.concatenate([x[..., None], y[..., None], z[..., None]], axis=-1)
        xyz = xyz @ k_inv.T
        y_axis = np.array([0.0, 1.0, 0.0], np.float32)
        x_axis = np.array([1.0, 0.0, 0.0], np.float32)
        R1, _ = cv2.Rodrigues(y_axis * np.radians(self.heading))
        R2, _ = cv2.Rodrigues(np.dot(R1, x_axis) * np.radians(self.pitch))
        R = R2 @ R1
        xyz = xyz @ R.T
        lng_lat = self.xyz_to_lng_lat(xyz) 
        xy = self.lng_lat_to_xy(lng_lat, shape=img.shape).astype(np.float32)
        persp = cv2.remap(img, xy[..., 0], xy[..., 1], cv2.INTER_CUBIC, borderMode=cv2.BORDER_WRAP)
        persp = persp[:, :, ::-1]
        return Image.fromarray(persp.astype("uint8")).convert("RGB")

    def xyz_to_lng_lat(self, xyz):
        norm = np.linalg.norm(xyz, axis=-1, keepdims=True)
        xyz_norm = xyz / norm
        x = xyz_norm[..., 0:1]
        y = xyz_norm[..., 1:2]
        z = xyz_norm[..., 2:]
        lon = np.arctan2(x, z)
        lat = np.arcsin(y)
        lst = [lon, lat]
        return np.concatenate(lst, axis=-1)

    def lng_lat_to_xy(self, lng_lat, shape: tuple[int, int]):
        X = (lng_lat[..., 0:1] / (2 * np.pi) + 0.5) * (shape[1] - 1)
        Y = (lng_lat[..., 1:] / (np.pi) + 0.5) * (shape[0] - 1)
        lst = [X, Y]
        return np.concatenate(lst, axis=-1)

    def has_borders(self, image: Image.Image) -> bool:
        for x in range(image.width):
            r, g, b = image.getpixel((x, image.height - 1))
            if not r == 0 or not g == 0 or not b == 0:
                return False
        for y in range(image.height):
            r, g, b = image.getpixel((image.width - 1, y))
            if not r == 0 or not g == 0 or not b == 0:
                return False
        return True

    def crop_borders(self, image: Image.Image) -> Image.Image:
        if not self.has_borders(image):
            return image
        return image.crop((0, 0, self.alt_tile_size * self.max_tiles_x, self.alt_tile_size * self.max_tiles_y))
