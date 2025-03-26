import os
import json
import pygame

class Character:
    def __init__(self, character_dir):
        self.character_dir = character_dir
        self.name = ""
        self.description = ""
        self.thumbnail = None
        self.actions = {}
        self.current_action = "idle"
        self.current_frame_index = 0
        self.frame_timer = 0

        self._load_character()

    def _load_character(self):
        json_path = os.path.join(self.character_dir, "character.json")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.name = data.get("name", "Unnamed")
        self.description = data.get("description", "")
        self.thumbnail = pygame.image.load(os.path.join(self.character_dir, data["thumbnail"])).convert_alpha()
        self.pos = pygame.Vector2(100, 100)
        self.vel = pygame.Vector2(0, 0)
        self.gravity = 1000  # pixels per second squared
        self.grounded = False

        actions = data.get("actions", {})
        for action_name, action_data in actions.items():
            frames = []
            action_dir = os.path.join(self.character_dir, "sprites", action_name)
            for frame in action_data.get("frames", []):
                image_path = os.path.join(action_dir, frame["image"])
                image = pygame.image.load(image_path).convert_alpha()
                duration = frame.get("duration", 1)
                frames.append({
                    "image": image,
                    "duration": duration
                })
            self.actions[action_name] = {
                "loop": action_data.get("loop", True),
                "frames": frames
            }

    def set_action(self, name):
        if name in self.actions and name != self.current_action:
            self.current_action = name
            self.current_frame_index = 0
            self.frame_timer = 0
            
    def get_current_frame(self):
        return self.actions[self.current_action]["frames"][self.current_frame_index]["image"]
            
    def apply_physics(self, dt, screen_height):
        if not self.grounded:
            self.vel.y += self.gravity * dt
            self.pos.y += self.vel.y * dt

            # Trigger falling animation if falling
            if self.vel.y > 0 and self.current_action != "fall":
                self.set_action("fall")

            # Floor collision
            floor_y = screen_height - self.get_current_frame().get_height()
            if self.pos.y >= floor_y:
                self.pos.y = floor_y
                self.vel.y = 0
                self.grounded = True
                self.set_action("idle")

    def update(self):
        action = self.actions[self.current_action]
        self.frame_timer += 1
        frame = action["frames"][self.current_frame_index]

        if self.frame_timer >= frame["duration"]:
            self.frame_timer = 0
            self.current_frame_index += 1
            if self.current_frame_index >= len(action["frames"]):
                if action["loop"]:
                    self.current_frame_index = 0
                else:
                    self.current_frame_index = len(action["frames"]) - 1  # Stay on last frame

    def draw(self, surface, pos):
        frame = self.actions[self.current_action]["frames"][self.current_frame_index]
        surface.blit(frame["image"], pos)
