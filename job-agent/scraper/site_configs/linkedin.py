LINKEDIN_CONFIG = {
  "name": "linkedin",
  "base_url": "https://www.linkedin.com/jobs",
  "scraper": "playwright",
  "selectors": {
    "job_card": ".base-card",
    "title": ".base-search-card__title",
    "company": ".base-search-card__subtitle",
    "location": ".job-search-card__location",
    "link": "a.base-card__full-link",
  },
  "search_param": "keywords",
}
