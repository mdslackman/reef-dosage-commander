# Universal Reef Dosage Calculator

A lightweight, brand-agnostic Python tool for reef aquarium maintenance. This tool calculates precise dosages for Alkalinity, Calcium, and Magnesium based on your specific system volume and any additive brand.

## Features
* **Brand Agnostic:** Works with Fritz, Red Sea, BRS, Seachem, or DIY additives.
* **AquaSpin Compatible:** Automatically detects and converts Alkalinity readings from ppm (AquaSpin standard) to dKH.
* **Safety Guardrails:** Automatically splits large doses over multiple days to prevent chemical shock:
    * **Alkalinity:** Max 1.0 dKH / day
    * **Calcium:** Max 20.0 ppm / day
    * **Magnesium:** Max 100.0 ppm / day

## How to use
1. **System Volume:** Enter your total water volume (gallons).
2. **Product Strength:** Look at your additive bottle. Find how much 1mL of the product raises 1 Gallon of water. 
   * *Example (Fritz Part 1):* 1mL adds 2.1 dKH to 1 Gallon. Enter **2.1**.
3. **Daily Dose:** The script provides a multi-day schedule to ensure your reef stays stable.

## Disclaimer
Always double-check calculations before dosing live animals. This tool is a guide; the health of your reef is your responsibility.
