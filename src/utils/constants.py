
import numpy as np

data_output_dict = None
default_data_dir = None
default_output_dir = None

config_defaults = {
    "default": {
        "data": default_data_dir,
        "output": default_output_dir,
        "license_key": "",
        "feature": 0,
        "active": True
    }
}

material_defaults = {
    "Aluminum": {
        "AlSi10Mg": {
            "name": "AlSi10Mg",
            "kt": 150,
            "rho": 2670,
            "cp": 900,
            "h": 10
        },
        "Al6061": {
            "name": "Al6061",
            "kt": 167,
            "rho": 2700,
            "cp": 895,
            "h": 10
        },
        "AlSi12": {
            "name": "AlSi12",
            "kt": 155,
            "rho": 2680,
            "cp": 890,
            "h": 10
        }
    },
    "Titanium": {
        "Ti6Al4V": {
            "name": "Ti6Al4V",
            "kt": 6.7,
            "rho": 4420,
            "cp": 560,
            "h": 15
        },
        "Pure Titanium": {
            "name": "Pure Titanium",
            "kt": 16.4,
            "rho": 4506,
            "cp": 520,
            "h": 15
        },
        "Ti-6Al-4V (Grade 5)": {
            "name": "Ti-6Al-4V (Grade 5)",
            "kt": 6.7,
            "rho": 4420,
            "cp": 560,
            "h": 15
        },
        "Ti-6Al-2Sn-4Zr-2Mo": {
            "name": "Ti-6Al-2Sn-4Zr-2Mo",
            "kt": 6.3,
            "rho": 4540,
            "cp": 570,
            "h": 15
        }
    },
    "Steel": {
        "316L Stainless Steel": {
            "name": "316L Stainless Steel",
            "kt": 14,
            "rho": 8000,
            "cp": 500,
            "h": 20
        },
        "304 Stainless Steel": {
            "name": "304 Stainless Steel",
            "kt": 14,
            "rho": 8000,
            "cp": 500,
            "h": 20
        },
        "Maraging Steel (18Ni300)": {
            "name": "Maraging Steel (18Ni300)",
            "kt": 14,
            "rho": 8000,
            "cp": 500,
            "h": 20
        }
    },
    "Nickel": {
        "Inconel 718": {
            "name": "Inconel 718",
            "kt": 11.4,
            "rho": 8190,
            "cp": 435,
            "h": 25
        },
        "Inconel 625": {
            "name": "Inconel 625",
            "kt": 9.8,
            "rho": 8440,
            "cp": 427,
            "h": 25
        }
    },
    "Copper": {
        "CuCrZr": {
            "name": "CuCrZr",
            "kt": 330,
            "rho": 8900,
            "cp": 385,
            "h": 35
        },
        "Pure Copper": {
            "name": "Pure Copper",
            "kt": 398,
            "rho": 8960,
            "cp": 385,
            "h": 35
        }
    },
    "Cobalt": {
        "CoCr": {
            "name": "CoCr",
            "kt": 14,
            "rho": 8500,
            "cp": 450,
            "h": 20
        }
    },
    "Nickel-Based Superalloys": {
        "Hastelloy X": {
            "name": "Hastelloy X",
            "kt": 11,
            "rho": 8220,
            "cp": 460,
            "h": 25
        }
    },
    "Stainless Steels": {
        "17-4 PH": {
            "name": "17-4 PH",
            "kt": 16,
            "rho": 7800,
            "cp": 500,
            "h": 20
        }
    },
    "Cobalt-Chromium Alloys": {
        "CoCrMo": {
            "name": "CoCrMo",
            "kt": 14,
            "rho": 8300,
            "cp": 460,
            "h": 22
        },
        "CoCrFeNiMn (High Entropy Alloys)": {
            "name": "CoCrFeNiMn (High Entropy Alloys)",
            "kt": 12.5,
            "rho": 7800,
            "cp": 480,
            "h": 22
        }
    },
    "Maraging Steels": {
        "18Ni-300": {
            "name": "18Ni-300",
            "kt": 14.5,
            "rho": 8000,
            "cp": 500,
            "h": 20
        }
    },
    "Tool Steels": {
        "H13 Tool Steel": {
            "name": "H13 Tool Steel",
            "kt": 28,
            "rho": 7750,
            "cp": 460,
            "h": 30
        }
    },
    "Refractory Metals": {
        "Tungsten (W)": {
            "name": "Tungsten (W)",
            "kt": 174,
            "rho": 19250,
            "cp": 134,
            "h": 50
        },
        "Tantalum (Ta)": {
            "name": "Tantalum (Ta)",
            "kt": 57.5,
            "rho": 16650,
            "cp": 140,
            "h": 45
        }
    },
    "Precious Metals": {
        "Gold Alloys": {
            "name": "Gold Alloys",
            "kt": 315,
            "rho": 19300,
            "cp": 129,
            "h": 35
        },
        "Platinum Alloys": {
            "name": "Platinum Alloys",
            "kt": 71.6,
            "rho": 21450,
            "cp": 133,
            "h": 38
        }
    },
    "Custom": {}
}

machine_defaults = {
    "Default": {
        "name": "Default",
        "vs": 300,
        "P": 100
    }
}

features = {
    "0": 2000,
    "1": 20000,
    "2": 200000,
    "3": 1000000,
    "4": np.inf
}
