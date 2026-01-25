"""
Astronomical Calculator using Science Skill Rules
Rule 2.3: Orbital mechanics calculations - Kepler's laws
Rule 6.1: Use astropy.constants for astronomical constants
Rule 6.2: Unit-aware calculations
"""

import numpy as np
from astropy import units as u
from astropy.constants import G, M_sun, R_sun


def calculate_stellar_density(mass: float, radius: float) -> dict:
    """
    Calculate stellar density using Science Skill Rule 6.2: Unit-aware calculations

    Args:
        mass: Stellar mass in solar masses
        radius: Stellar radius in solar radii

    Returns:
        dict: Density calculation results with proper units
    """
    # Convert to SI units - Rule 6.2: Unit-aware calculations
    mass_si = mass * M_sun
    radius_si = radius * R_sun

    # Calculate volume using vectorized operations - Rule 1.2
    volume = (4 / 3) * np.pi * radius_si**3

    # Calculate density
    density = mass_si / volume

    return {
        "density": density.to(u.g / u.cm**3),  # Convert to cgs units
        "mass_solar": mass,
        "radius_solar": radius,
        "method": "Science Skill Rule 6.2 - Unit-aware calculations",
    }


def calculate_orbital_period(semi_major_axis: float, central_mass: float) -> dict:
    """
    Calculate orbital period using Kepler's third law
    Rule 2.3: Orbital mechanics calculations

    Args:
        semi_major_axis: Semi-major axis in AU
        central_mass: Central mass in solar masses

    Returns:
        dict: Orbital period calculation
    """
    # Use astropy constants - Rule 6.1
    a = semi_major_axis * u.au
    M = central_mass * M_sun

    # Kepler's third law: P² = 4π²/GM * a³
    period_squared = (4 * np.pi**2 / (G * M)) * a**3
    period = np.sqrt(period_squared)

    return {
        "period_years": period.to(u.year).value,
        "period_days": period.to(u.day).value,
        "semi_major_axis_au": semi_major_axis,
        "central_mass_solar": central_mass,
        "method": "Science Skill Rule 2.3 - Kepler's third law",
    }


def validate_astronomical_data(ra: float, dec: float, magnitude: float) -> dict:
    """
    Validate astronomical observation data
    Rule 8.1: Scientific data validation

    Args:
        ra: Right ascension in degrees
        dec: Declination in degrees
        magnitude: Apparent magnitude

    Returns:
        dict: Validation results
    """
    from astropy.coordinates import SkyCoord

    errors = []
    warnings = []

    # Validate coordinates - Rule 8.1
    try:
        coords = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
    except ValueError as e:
        errors.append(f"Invalid coordinates: {e}")
        return {"valid": False, "errors": errors, "warnings": warnings}

    # Validate magnitude range - Rule 8.1
    if not (-50 <= magnitude <= 50):
        errors.append(f"Magnitude {magnitude} out of valid range [-50, 50]")
    elif magnitude < -10:
        warnings.append(f"Very bright magnitude {magnitude} - possible supernova or error")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "coordinates": coords,
        "method": "Science Skill Rule 8.1 - Scientific data validation",
    }


# Example usage demonstrating Science Skill rules
if __name__ == "__main__":
    # Sun density calculation
    sun_density = calculate_stellar_density(1.0, 1.0)
    print(f"Sun density: {sun_density['density']:.2f}")

    # Earth orbital period
    earth_orbit = calculate_orbital_period(1.0, 1.0)
    print(f"Earth orbital period: {earth_orbit['period_years']:.2f} years")

    # Validate Sirius coordinates (brightest star)
    sirius_validation = validate_astronomical_data(101.287, -16.716, -1.46)
    print(f"Sirius validation: {'Valid' if sirius_validation['valid'] else 'Invalid'}")
