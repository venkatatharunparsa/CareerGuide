from scraper.site_configs.internshala import INTERNSHALA_CONFIG
from scraper.site_configs.linkedin import LINKEDIN_CONFIG
from scraper.site_configs.naukri import NAUKRI_CONFIG

SITE_CONFIGS = {
  "linkedin": LINKEDIN_CONFIG,
  "naukri": NAUKRI_CONFIG,
  "internshala": INTERNSHALA_CONFIG,
}

__all__ = ["SITE_CONFIGS", "LINKEDIN_CONFIG", "NAUKRI_CONFIG", "INTERNSHALA_CONFIG"]
