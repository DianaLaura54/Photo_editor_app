import os
import numpy as np
import cv2
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.slider import Slider
from kivy.uix.camera import Camera
from kivy.utils import get_color_from_hex

class Thumbnail(ButtonBehavior, Image):
    def __init__(self, image_path, **kwargs):
        super().__init__(**kwargs)
        self.image_path = image_path
        self.source = self.image_path
        self.size_hint = (None, None)
        self.size = (150, 150)
        self.allow_stretch = True
        self.keep_ratio = True

    def on_press(self):
        self.parent.parent.show_full_image(self.image_path)


class ImageList(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.current_image_path = None
        self.full_image = None
        self.red_channel_image_path = None
        self.green_channel_image_path = None
        self.blue_channel_image_path = None
        self.thumbnail_grid = GridLayout(cols=8, spacing=2, size_hint_y=5)
        self.thumbnail_grid.bind(minimum_height=self.thumbnail_grid.setter('height'))
        self.load_images()

    def load_images(self):
        self.clear_split_channels_images()
        self.current_image_path = None  # Reset the current image path
        self.clear_widgets()
        self.add_widget(self.thumbnail_grid)
        self.thumbnail_grid.clear_widgets()
        for filename in os.listdir("images"):
            if filename.endswith(".png") or filename.endswith(".jpg"):
                image_path = os.path.join("images", filename)
                thumbnail = Thumbnail(image_path=image_path)
                self.thumbnail_grid.add_widget(thumbnail)

        camera_button = Button(text="Open Camera", size_hint=(None, None), size=(150, 40), background_color=get_color_from_hex("#FF69B4"))
        camera_button.bind(on_press=lambda x: self.open_camera())
        self.add_widget(camera_button)

    def open_camera(self):
        self.clear_widgets()
        camera_layout = BoxLayout(orientation='vertical')
        self.camera = Camera(play=True)
        camera_layout.add_widget(self.camera)

        capture_button = Button(text="Capture", size_hint=(None, None), size=(150, 40), background_color=get_color_from_hex("#FF69B4"))
        capture_button.bind(on_press=lambda x: self.capture_image())
        camera_layout.add_widget(capture_button)

        self.add_widget(camera_layout)

    def capture_image(self):
        if not hasattr(self, 'camera') or not self.camera:
            return

        if self.camera.play:
            self.camera.export_to_png("captured_image.png")
            self.show_full_image("captured_image.png")
            self.camera.play = False
        else:

            self.clear_widgets()
            camera_layout = BoxLayout(orientation='vertical')
            self.camera = Camera(play=True)
            camera_layout.add_widget(self.camera)

            def capture_and_update_image():
                self.camera.export_to_png("captured_image.png")
                self.show_full_image("captured_image.png")

            capture_button = Button(text="Capture", size_hint=(None, None), size=(150, 40), background_color=get_color_from_hex("#FF69B4"))
            capture_button.bind(on_press=lambda x: capture_and_update_image())
            camera_layout.add_widget(capture_button)

            self.add_widget(camera_layout)

    def show_full_image(self, image_path):
        self.clear_widgets()
        self.current_image_path = image_path
        self.full_image = Image(source=image_path)
        self.add_widget(self.full_image)

        button_layout = BoxLayout(size_hint=(1, 0.1), orientation='vertical')

        back_button = Button(text="Back", size_hint=(None, None), size=(100, 40), background_color=get_color_from_hex("#FF69B4"))
        back_button.bind(on_press=lambda x: self.load_images())
        button_layout.add_widget(back_button)

        flip_button = Button(text="Flip H", size_hint=(None, None), size=(100, 40), background_color=get_color_from_hex("#FF69B4"))
        flip_button.bind(on_press=lambda x: self.flip_image("horizontal"))
        button_layout.add_widget(flip_button)

        flip_button_v = Button(text="Flip V", size_hint=(None, None), size=(100, 40), background_color=get_color_from_hex("#FF69B4"))
        flip_button_v.bind(on_press=lambda x: self.flip_image("vertical"))
        button_layout.add_widget(flip_button_v)

        invert_button = Button(text="Invert", size_hint=(None, None), size=(100, 40), background_color=get_color_from_hex("#FF69B4"))
        invert_button.bind(on_press=lambda x: self.invert_image())
        button_layout.add_widget(invert_button)

        resize_button = Button(text="Resize", size_hint=(None, None), size=(100, 40), background_color=get_color_from_hex("#FF69B4"))
        resize_button.bind(on_press=lambda x: self.resize_image())
        button_layout.add_widget(resize_button)

        split_channels_button = Button(text="Split Channels", size_hint=(None, None), size=(120, 40), background_color=get_color_from_hex("#FF69B4"))
        split_channels_button.bind(on_press=lambda x: self.split_channels_image())
        button_layout.add_widget(split_channels_button)

        hsv_button = Button(text="Convert to HSV", size_hint=(None, None), size=(150, 40), background_color=get_color_from_hex("#FF69B4"))
        hsv_button.bind(on_press=lambda x: self.convert_to_hsv())
        button_layout.add_widget(hsv_button)

        lightness_slider = Slider(min=-100, max=100, value=0, size_hint=(1, None), height=40)
        lightness_slider.bind(value=self.on_lightness_change)
        button_layout.add_widget(lightness_slider)

        grayscale_button = Button(text="Grayscale", size_hint=(None, None), size=(100, 40), background_color=get_color_from_hex("#FF69B4"))
        grayscale_button.bind(on_press=lambda x: self.convert_to_grayscale())
        button_layout.add_widget(grayscale_button)

        self.add_widget(button_layout)
        self.lightness_slider = lightness_slider

    def clear_split_channels_images(self):
        self.clear_widgets()
        self.current_image_path = None
        self.full_image = None

    def flip_image(self, direction):
        img_array = self.load_image_to_array(self.current_image_path)
        if direction == "horizontal":
            flipped_image = self.mirror_h(img_array)
        else:
            flipped_image = self.mirror_v(img_array)
        flipped_image = np.array(flipped_image, dtype=np.uint8)
        temp_image_path = "temp_flipped_image.jpg"
        self.save_array_to_image(flipped_image, temp_image_path)
        self.full_image.source = temp_image_path
        self.full_image.reload()

    def invert_image(self):
        try:
            img_array = self.load_image_to_array(self.current_image_path)
            inverted_image = self.invert(img_array)
            temp_image_path = "temp_inverted_image.jpg"
            self.save_array_to_image(inverted_image, temp_image_path)
            self.full_image.source = temp_image_path
            self.full_image.reload()
        except Exception as e:
            print("Error inverting image:", e)

    def invert(self, img):
        inverted_img = np.array([[[255 - k for k in j] for j in i] for i in img], dtype=np.uint8)
        return inverted_img

    def resize_image(self):
        try:
            img_array = self.load_image_to_array(self.current_image_path)
            new_size = (300, 300)
            resized_image = self.resize(img_array, new_size)
            temp_image_path = "temp_resized_image.jpg"
            self.save_array_to_image(resized_image, temp_image_path)
            self.full_image.source = temp_image_path
            self.full_image.reload()
        except Exception as e:
            print("Error resizing image:", e)

    def resize(self, img, size):
        resized_img = np.array([[
            [img[int(len(img) * i / size[0])][int(len(img[0]) * j / size[1])][k]
             for k in range(3)] for j in range(size[1])] for i in range(size[0])], dtype=np.uint8)
        return resized_img

    def lightness(self, img, b=50):
        b = b / 100
        adjusted_img = np.clip(((1 - b) * img + b * 255).astype(np.uint8), 0, 255)
        return adjusted_img

    def on_lightness_change(self, instance, value):
        try:
            img_array = self.load_image_to_array(self.current_image_path)
            adjusted_img = self.lightness(img_array, value)
            temp_image_path = "temp_lightness_image.jpg"
            self.save_array_to_image(adjusted_img, temp_image_path)
            self.full_image.source = temp_image_path
            self.full_image.reload()
        except Exception as e:
            print("Error adjusting lightness:", e)

    def split_channels_image(self):
        try:
            img_array = self.load_image_to_array(self.current_image_path)
            height, width = img_array.shape[:2]

            dst_r = np.zeros((height, width, 3), dtype=np.uint8)
            dst_g = np.zeros((height, width, 3), dtype=np.uint8)
            dst_b = np.zeros((height, width, 3), dtype=np.uint8)
            for i in range(height):
                for j in range(width):
                    b, g, r = img_array[i, j]
                    dst_b[i, j] = [b, 0, 0]
                    dst_g[i, j] = [0, g, 0]
                    dst_r[i, j] = [0, 0, r]

            self.show_channel_images(dst_r, dst_g, dst_b)
        except Exception as e:
            print("Error splitting channels:", e)

    def show_channel_images(self, red_array, green_array, blue_array):
        cv2.imshow('Red Channel', red_array)
        cv2.imshow('Green Channel', green_array)
        cv2.imshow('Blue Channel', blue_array)

    def load_image_to_array(self, image_path):
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert to RGB
        return img

    def save_array_to_image(self, img_array, image_path):
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)  # Convert back to BGR
        cv2.imwrite(image_path, img_array)

    def mirror_h(self, img):
        return [[img[i][-j - 1] for j in range(len(img[0]))] for i in range(len(img))]

    def mirror_v(self, img):
        return [img[-i - 1] for i in range(len(img))]


    def convert_to_grayscale(self):
        try:
            img_array = self.load_image_to_array(self.current_image_path)
            gray_img = self.grayscale(img_array)
            temp_image_path = "temp_gray_image.jpg"
            self.save_array_to_image(gray_img, temp_image_path)
            self.full_image.source = temp_image_path
            self.full_image.reload()
        except Exception as e:
            print("Error converting to grayscale:", e)

    def grayscale(self, img):
        try:
            height, width, _ = img.shape
            gray_img = np.zeros((height, width), dtype=np.uint8)

            for i in range(height):
                for j in range(width):
                    r = img[i, j, 2] / 255.0
                    g = img[i, j, 1] / 255.0
                    b = img[i, j, 0] / 255.0


                    gray_intensity = (r / 3 + g / 3 + b / 3) * 255

                    gray_img[i, j] = int(gray_intensity)

            return gray_img
        except Exception as e:
            print("Error in grayscale conversion:", e)


    def convert_to_hsv(self, instance=None):
        try:
            img_array = self.load_image_to_array(self.current_image_path)
            height, width, _ = img_array.shape
            hsv_img = np.zeros((height, width, 3), dtype=np.uint8)

            for i in range(height):
                for j in range(width):
                    r = img_array[i, j, 2] / 255.0
                    g = img_array[i, j, 1] / 255.0
                    b = img_array[i, j, 0] / 255.0

                    M = max(r, g, b)
                    m = min(r, g, b)
                    C = M - m
                    V = M

                    if V != 0:
                        S = C / V
                    else:
                        S = 0

                    if C != 0:
                        if M == r:
                            H = 60 * (g - b) / C
                        elif M == g:
                            H = 120 + 60 * (b - r) / C
                        elif M == b:
                            H = 240 + 60 * (r - g) / C
                    else:
                        H = 0

                    if H < 0:
                        H += 360

                    H_norm = H * 255 / 360
                    S_norm = S * 255
                    V_norm = V * 255

                    hsv_img[i, j, 0] = H_norm
                    hsv_img[i, j, 1] = S_norm
                    hsv_img[i, j, 2] = V_norm

            convH = hsv_img[:, :, 0]
            convS = hsv_img[:, :, 1]
            convV = hsv_img[:, :, 2]
            self.show_hsv_images(convH, convS, convV)
        except Exception as e:
            print("Error converting to HSV:", e)

    def show_hsv_images(self, h_array, s_array, v_array):
        cv2.imshow('H Channel', h_array)
        cv2.imshow('S Channel', s_array)
        cv2.imshow('V Channel', v_array)


class ImageViewerApp(App):
    def build(self):
        return ImageList()

if __name__ == "__main__":
    ImageViewerApp().run()