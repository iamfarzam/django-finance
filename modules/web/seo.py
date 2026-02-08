"""SEO-related views and utilities."""

from django.contrib.sitemaps import Sitemap
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages."""

    priority = 0.5
    changefreq = "weekly"

    def items(self):
        """Return list of static pages."""
        return []

    def location(self, item):
        """Return URL for each item."""
        return reverse(item)


def robots_txt(request: HttpRequest) -> HttpResponse:
    """Serve robots.txt."""
    return render(request, "robots.txt", content_type="text/plain")
