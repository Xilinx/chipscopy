# Copyright (C) 2025-2026, Advanced Micro Devices, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
from dataclasses import dataclass, field
from typing import List, Dict
from pathlib import Path


@dataclass
class SupportedExamples:
    examples: set = field(default_factory=set)
    hw_platforms: set = field(default_factory=set)
    platform_example_map: Dict[str, set] = field(default_factory=dict)

    def add_example(self, example: str):
        self.examples.add(example)

    def add_hw_platform(self, hw_platform: str):
        self.hw_platforms.add(hw_platform)

    def add_to_platform_map(self, platform: str, example: str):
        if platform not in self.platform_example_map:
            self.platform_example_map[platform] = set()
        self.platform_example_map[platform].add(example)


def find_manifest_files(base_dir):
    manifest_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file == "manifest.json":
                manifest_files.append(os.path.join(root, file))
    return manifest_files


def load_and_print_manifest(file_path):
    try:
        with open(file_path, "r") as file:
            manifest_data = json.load(file)

        def print_fields(data, indent=0):
            for key, value in data.items():
                if isinstance(value, dict):
                    print(" " * indent + f"{key}:")
                    print_fields(value, indent + 4)
                elif isinstance(value, list):
                    print(" " * indent + f"{key}:")
                    for item in value:
                        if isinstance(item, dict):
                            print_fields(item, indent + 4)
                        else:
                            print(" " * (indent + 4) + str(item))
                else:
                    print(" " * indent + f"{key}: {value}")

        print_fields(manifest_data)

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from '{file_path}'.")


def create_supported_examples(manifest_files):
    supported_examples = SupportedExamples()
    for file in manifest_files:
        if file.endswith(".json"):
            try:
                with open(file, "r") as manifest_file:
                    manifest_data = json.load(manifest_file)

                    platforms = manifest_data["example"]["exampleDescription"]["platforms"]
                    example_id = manifest_data["example"]["exampleID"]

                    if isinstance(platforms, str):
                        platforms = [platforms]

                    if platforms:
                        for platform in platforms:
                            supported_examples.add_hw_platform(platform)
                    if example_id:
                        supported_examples.add_example(example_id)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error reading manifest file {file}: {e}")

            # Update example_platform_map
            for platform in platforms:
                supported_examples.add_to_platform_map(platform, example_id)

    return supported_examples


this_file = Path(__file__)
base_directory = this_file.parent.parent.joinpath("examples")
manifest_files = find_manifest_files(base_directory)
supported_examples = create_supported_examples(manifest_files)
print(supported_examples.platform_example_map)

# print("Loaded manifest files:")
# for manifest in manifest_files:
#     load_and_print_manifest(manifest)
