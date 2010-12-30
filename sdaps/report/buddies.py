# -*- coding: utf-8 -*-
# SDAPS - Scripts for data acquisition with paper based surveys
# Copyright (C) 2008, Christoph Simon <christoph.simon@gmx.eu>
# Copyright (C) 2008, Benjamin Berg <benjamin@sipsolutions.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import math

from reportlab import platypus
from reportlab.lib import styles
from reportlab.lib import colors
from reportlab.lib import units

from sdaps import clifilter
from sdaps import template
from sdaps import model

import flowables
import answers

from sdaps import calculate


mm = units.mm


stylesheet = dict(template.stylesheet)

stylesheet['Head'] = styles.ParagraphStyle(
	'Head',
	stylesheet['Normal'],
	fontSize = 12,
	leading = 17,
	backColor = colors.lightgrey,
	spaceBefore = 5 * mm,
)

stylesheet['Question'] = styles.ParagraphStyle(
	'Question',
	stylesheet['Normal'],
	spaceBefore = 3 * mm,
	fontName = 'Times-Bold',
)


class Questionnaire (model.buddy.Buddy) :

	__metaclass__ = model.buddy.Register
	name = 'report'
	obj_class = model.questionnaire.Questionnaire

	def init (self, small = 0) :
		self.small = small
		# iterate over qobjects
		for qobject in self.obj.qobjects :
			qobject.report.init(small)

	def report (self) :
		# iterate over qobjects
		for qobject in self.obj.qobjects :
			qobject.report.report()

	def story (self) :
		story = list()
		# iterate over qobjects
		for qobject in self.obj.qobjects :
			story.extend(list(qobject.report.story()))
		return story

	def filters (self) :
		filters = list()
		# iterate over qobjects
		for qobject in self.obj.qobjects :
			filters.extend(list(qobject.report.filters()))
		return filters


class QObject (model.buddy.Buddy) :

	__metaclass__ = model.buddy.Register
	name = 'report'
	obj_class = model.questionnaire.QObject

	def init (self, small) :
		self.small = small

	def report (self) :
		pass

	def story (self) :
		return []

	def filters (self) :
		return []


class Head (QObject) :

	__metaclass__ = model.buddy.Register
	name = 'report'
	obj_class = model.questionnaire.Head

	def story (self) :
		return [
			platypus.Paragraph(
		        u'%i. %s' % (self.obj.id[0], self.obj.title),
		        stylesheet['Head'])]


class Question (QObject) :

	__metaclass__ = model.buddy.Register
	name = 'report'
	obj_class = model.questionnaire.Question

	def story (self) :
		return [
			platypus.Paragraph(
		        u'%i.%i %s' % (
		            self.obj.id[0], self.obj.id[1], self.obj.question),
		        stylesheet['Question'])]


class Choice (Question) :

	__metaclass__ = model.buddy.Register
	name = 'report'
	obj_class = model.questionnaire.Choice

	def init (self, small) :
		self.small = small
		self.text = list()

	def report (self) :
		if not self.small :
			for box in self.obj.boxes :
				if (isinstance(box, model.questionnaire.Textbox) and
				    box.data.state) :
					self.text.append(answers.Text(box))

	def story (self) :
		story = Question.story(self)
		if self.obj.calculate.count :
			for box in self.obj.boxes :
				story.append(
					answers.Choice(
						box.text,
						self.obj.calculate.values[box.value],
						self.obj.calculate.significant[box.value]
					)
				)
			story = [platypus.KeepTogether(story)]
			if len(self.text) > 0 :
				story.append(platypus.Spacer(0, 3 * mm))
				story.extend(self.text)
		return story

	def filters (self) :
		for box in self.obj.boxes :
			yield u'%i in _%i_%i' % (box.value, self.obj.id[0], self.obj.id[1])


class Mark (Question) :

	__metaclass__ = model.buddy.Register
	name = 'report'
	obj_class = model.questionnaire.Mark

	def story (self) :
		story = Question.story(self)
		if self.obj.calculate.count :
			story.append(answers.Mark(
				self.obj.calculate.values.values(),
			    self.obj.answers,
			    self.obj.calculate.mean,
			    self.obj.calculate.standard_derivation,
			    self.obj.calculate.count,
			    self.obj.calculate.significant))
			story = [platypus.KeepTogether(story)]
		return story

	def filters (self) :
		for x in range(6) :
			yield u'%i == _%i_%i' % (x, self.obj.id[0], self.obj.id[1])


class Text (Question) :

	__metaclass__ = model.buddy.Register
	name = 'report'
	obj_class = model.questionnaire.Text

	def init (self, small) :
		self.small = small
		self.text = list()

	def report (self) :
		if not self.small :
			for box in self.obj.boxes :
				if box.data.state :
					self.text.append(answers.Text(box))

	def story (self) :
		story = Question.story(self)
		if len(self.text) > 0 :
			story.append(self.text[0])
			story = [platypus.KeepTogether(story)]
		if len(self.text) > 1 :
			story.extend(self.text[1:])
		return story


class Additional_FilterHistogram (Question) :

	__metaclass__ = model.buddy.Register
	name = 'report'
	obj_class = model.questionnaire.Additional_FilterHistogram

	def story (self) :
		story = Question.story(self)
		if self.obj.calculate.count :
			for i in range(len(self.obj.calculate.values)) :
				story.append(
					answers.Choice(
						self.obj.answers[i],
						self.obj.calculate.values[i],
						self.obj.calculate.significant[i]
					)
				)
			story = [platypus.KeepTogether(story)]
		return story