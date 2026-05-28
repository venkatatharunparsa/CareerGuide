INTERNSHALA_CONFIG = {
  "name": "internshala",
  "base_url": "https://internshala.com",
  "scraper": "bs4",
  "selectors": {
    "job_card": ".individual_internship",
    "title": "h3 a",
    "company": ".company_name",
    "location": ".locations",
    "link": "h3 a",
  },
  "search_param": "search",
}
