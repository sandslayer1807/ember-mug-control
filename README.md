# Ember Mug Control

## Introduction

This mini 'application' was just something written to help interact with my Ember Mug, as the official app (at the time) was giving me a lot of issues.

After some digging around, I found [this lovely repository](https://github.com/orlopau/ember-mug) that details the hows of interacting with the mug over BLE. A couple of beers (and hours) later and this was born!

## Functionality

This application lets you do things like:
- See the status (battery percentage, charging status, current & target temperatures)
- Update various operating parameters (temperature, temperature unit, name)

## Roadmap

There's a couple of things I may or may not add as time goes on, ranging from:
- A desperate need of method documentation
- Refactoring the very simple CLI to a GUI or a more complex CLI utilizing [asciimatics](https://pypi.org/project/asciimatics/)
- Adding persistence of any interacted-with mugs for quicker startup of the app with less command-line wrangling.
  - This would allow things like using the mug's name in the prompts instead of the default 'Ember Ceramic Mug'.

## Remarks

This application is _definitely_ not perfect, and was written in haste. Feel free to extend this or the original documentation with any new / desired features as you stumble upon the need.

**To Warm Coffee!**
