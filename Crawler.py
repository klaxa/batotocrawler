#!/usr/bin/python

from abc import ABCMeta, abstractmethod

class Crawler(metaclass=ABCMeta):
	@abstractmethod
	def __init__(self, url):
		pass
	
	@abstractmethod
	def chapter_info(self, chapter_data):
		pass
	
	@abstractmethod
	def chapter_pages(self, chapter_url):
		pass
	
	@abstractmethod
	def chapter_images(self, chapter_url):
		pass
	
	@abstractmethod
	def series_chapters(self):
		pass
	
	@abstractmethod
	def series_info(self, search):
		pass
