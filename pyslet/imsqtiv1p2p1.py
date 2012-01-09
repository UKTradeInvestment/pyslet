#! /usr/bin/env python
"""This module implements the QTI 1.2.1 specification defined by IMS GLC
"""

import pyslet.xml20081126 as xml
import pyslet.imsqtiv2p1 as qtiv2
import pyslet.imsmdv1p2p1 as imsmd
import pyslet.html40_19991224 as html
import pyslet.xsdatatypes20041028 as xsi
import pyslet.rfc2396 as uri

import string, codecs
import os.path
from types import StringTypes

#IMSQTI_NAMESPACE="http://www.imsglobal.org/xsd/ims_qtiasiv1p2"
QTI_SOURCE='QTIv1'


class QTIError(Exception): pass
class QTIUnimplementedError(QTIError): pass
class QTIIndexInMultiple: pass

def MakeValidName(name):
	"""This function takes a string that is supposed to match the
	production for Name in XML and forces to to comply by replacing
	illegal characters with '_'.  If name starts with a valid name
	character but not a valid name start character, it is prefixed
	with '_' too."""
	if name:
		goodName=[]
		if not xml.IsNameStartChar(name[0]):
			goodName.append('_')
		for c in name:
			if xml.IsNameChar(c):
				goodName.append(c)
			else:
				goodName.append('_')
		return string.join(goodName,'')
	else:
		return '_'

def ParseYesNo(src):
	return src.strip().lower()=='yes'

def FormatYesNo(value):
	if value:
		return 'Yes'
	else:
		return 'No'

def ParseInteger(src):
	try:
		return int(src)
	except:
		return None

def FormatInteger(value):
	return "%i"%value


class QTIArea:
	"""Area enumeration::
	
	(Ellipse | Rectangle | Bounded )  'Ellipse'
	"""
	decode={
		'Ellipse':1,
		'Rectangle':2,
		'Bounded':3
		}
xsi.MakeEnumeration(QTIArea)

def DecodeArea(value):
	"""Decodes an area value from a string."""
	try:
		value=value.strip()
		value=value[0].upper()+value[1:].lower()
		return QTIArea.decode[value]
	except KeyError:
		raise ValueError("Can't decode area from %s"%value)

def EncodeArea(value):
	return QTIArea.encode.get(value,None)


class QTIFIBType:
	"""fibtype enumeration::
	
	fibtype      (String | Integer | Decimal | Scientific )  'String'
	"""
	decode={
		'String':1,
		'Integer':2,
		'Decimal':3,
		'Scientific':4
		}
xsi.MakeEnumeration(QTIFIBType)

def DecodeFIBType(value):
	"""Decodes a fibtype value from a string."""
	try:
		value=value.strip()
		value=value[0].upper()+value[1:].lower()
		return QTIFIBType.decode[value]
	except KeyError:
		raise ValueError("Can't decode fibtype from %s"%value)

def EncodeFIBType(value):
	return QTIFIBType.encode.get(value,None)


class NumType:
	"""numtype enumeration::
	
	numtype      (Integer | Decimal | Scientific )  'Integer'
	"""
	decode={
		'Integer':1,
		'Decimal':2,
		'Scientific':3
		}
xsi.MakeEnumeration(NumType)

def DecodeNumType(value):
	"""Decodes a fibtype value from a string."""
	try:
		value=value.strip()
		value=value[0].upper()+value[1:].lower()
		return NumType.decode[value]
	except KeyError:
		raise ValueError("Can't decode numtype from %s"%value)

def EncodeNumType(value):
	return NumType.encode.get(value,None)


class QTIPromptType:
	"""prompt enumeration::
	
	prompt       (Box | Dashline | Asterisk | Underline )"""
	decode={
		'Box':1,
		'Dashline':2,
		'Asterisk':3,
		'Underline':4
		}
xsi.MakeEnumeration(QTIPromptType)

def DecodePromptType(value):
	"""Decodes a prompt value from a string."""
	try:
		value=value.strip()
		value=value[0].upper()+value[1:].lower()
		return QTIPromptType.decode[value]
	except KeyError:
		raise ValueError("Can't decode prompt from %s"%value)

def EncodePromptType(value):
	return QTIPromptType.encode.get(value,None)


class QTIOrientation:
	"""Orientation enumeration::
	
	(Horizontal | Vertical )  'Horizontal'
	"""
	decode={
		'Horizontal':1,
		'Vertical':2,
		}
xsi.MakeEnumeration(QTIOrientation)

V2ORIENTATION_MAP={
	QTIOrientation.Horizontal:qtiv2.Orientation.horizontal,
	QTIOrientation.Vertical:qtiv2.Orientation.vertical
	}

def DecodeOrientation(value):
	"""Decodes an orientation value from a string."""
	try:
		value=value.strip()
		value=value[0].upper()+value[1:].lower()
		return QTIOrientation.decode[value]
	except KeyError:
		raise ValueError("Can't decode orientation from %s"%value)

def EncodeOrientation(value):
	return QTIOrientation.encode.get(value,'Horizontal')


def MigrateV2AreaCoords(area,value,log):
	"""Given a v1 area returns a v2 shape,coords array.

	This conversion is generous because the separators have never been well
	defined and in some cases content use a mixture of space and ','.

	Note also that the definition of rarea was updated in the 1.2.1 errata and
	this affects this algorithm.  The clarification on the definition of ellipse
	from radii to diameters might mean that some content ends up with hotspots
	that are too small but this is safer than hotspots that are too large."""
	coords=[]
	vStr=[]
	sep=0
	for c in value:
		if c in "0123456789.":
			if sep and vStr:
				coords.append(int(float(string.join(vStr,''))))
				sep=0
				vStr=[]
			vStr.append(c)
		else:
			sep=1
	if vStr:
		coords.append(int(float(string.join(vStr,''))))
	if area==QTIArea.Rectangle:
		if len(coords)<4:
			log.append("Error: not enough coordinates for rectangle, padding with zeros")
			while len(coords)<4:
				coords.append(0)
		shape=qtiv2.QTIShape.rect
		coords=[coords[0],coords[1],coords[0]+coords[3]-1,coords[1]+coords[2]-1]
	elif area==QTIArea.Ellipse:
		if len(coords)<4:
			if len(corrds)<2:
				log.append("Error: not enough coordinates to locate ellipse, padding with zero")
				while len(coords)<2:
					coords.append(0)
			if len(coords)==2:
				log.append("Error: ellipse has no radius, treating as circule radius 4")
				coords=coords+[8,8]
			elif len(coords)==3:
				log.append("Error: only one radius given for ellipse, assuming circular")
				coords.append(coords[-1])
		if coords[2]==coords[3]:
			r=coords[2]/2 # centre-pixel coordinate model again
			coords=[coords[0],coords[1],r]
			shape=qtiv2.QTIShape.circle
		else:
			log.warning("Warning: ellipse shape is deprecated in version 2")
			coords=[coords[0],coords[1],coords[2]/2,coords[3]/2]
			shape=qtiv2.QTIShape.ellipse
	else:
		shape=qtiv2.QTIShape.poly
	return shape,coords

		
class QTIElement(xml.XMLElement):
	"""Basic element to represent all QTI elements"""
	
	def DeclareMetadata(self,label,entry,definition=None):
		"""Declares a piece of metadata associated with the element.
		
		Most QTIElements will be contained by some type of metadata container
		that collects metadata in a format suitable for easy lookup and export
		to other metadata formats.  The default implementation simply passes the
		call to the parent QTIElement or ignores the definition"""
		if isinstance(self.parent,QTIElement):
			self.parent.DeclareMetadata(label,entry,definition)
		else:
			pass


class QTICommentElement(QTIElement):
	"""Basic element to represent all QTI elements that contain a comment as first element.
	
::

	<!ELEMENT XXXXXXXXXXXX (qticomment? , ....... )>"""
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		self.QTIComment=None

	def GetChildren(self):
		if self.QTIComment:
			return [self.QTIComment]
		else:
			return []


#
#	ROOT DEFINITION
#
class QTIQuesTestInterop(QTICommentElement):
	"""<!ELEMENT questestinterop (qticomment? , (objectbank | assessment | (section | item)+))>"""
	XMLNAME='questestinterop'

	def __init__(self,parent):
		QTICommentElement.__init__(self,parent)
		self.QTIObjectBank=None
		self.QTIAssessment=None
		self.objectList=[]
	
	def GetChildren(self):
		children=QTICommentElement.GetChildren(self)
		if self.QTIObjectBank:
			children.append(self.QTIObjectBank)
		elif self.QTIAssessment:
			children.append(self.QTIAssessment)
		else:
			children=children+self.objectList
		return children

	def QTIItem(self):
		child=QTIItem(self)
		self.objectList.append(child)
		return child
		
	def MigrateV2(self):
		"""Converts this element to QTI v2
		
		Returns a list of tuples of the form:
		( <QTIv2 Document>, <Metadata>, <List of Log Messages> ).
		
		One tuple is returned for each of the objects found. In QTIv2 there is
		no equivalent of QuesTestInterop.  The baseURI of each document is set
		from the baseURI of the QuesTestInterop element using the object
		identifier to derive a file name."""
		output=[]
		# ignore QTIObjectBank for the moment
		# ignore QTIAssessment for the moment
		if self.QTIAssessment:
			self.QTIAssessment.MigrateV2(output)
		for object in self.objectList:
			object.MigrateV2(output)
		if self.QTIComment:
			if self.QTIObjectBank:
				# where to put the comment?
				pass
			elif self.QTIAssessment:
				if len(self.objectList)==0:
					# Add this comment as a metadata description on the assessment
					pass
			elif len(self.objectList)==1:
				# Add this comment to this object's metdata description
				doc,lom,log=output[0]
				general=lom.LOMGeneral()
				description=general.LOMDescription().LangString()
				description.SetValue(self.QTIComment.GetValue())
		return output


#
#	ENTITY DEFINITIONS
#
"""
These definitions are used for common attribute definitions in the specification
and map to mix-in classes to make implementing these attribute pattern easier.

<!ENTITY % I_Testoperator " testoperator  (EQ | NEQ | LT | LTE | GT | GTE )  #REQUIRED">

<!ENTITY % I_Pname " pname CDATA  #REQUIRED">

<!ENTITY % I_Class " class CDATA  'Block'">

<!ENTITY % I_Mdoperator " mdoperator  (EQ | NEQ | LT | LTE | GT | GTE )  #REQUIRED">

<!ENTITY % I_Mdname " mdname CDATA  #REQUIRED">

<!ENTITY % I_Title " title CDATA  #IMPLIED">

<!ENTITY % I_Label " label CDATA  #IMPLIED">

<!ENTITY % I_Ident " ident CDATA  #REQUIRED">
"""

class QTIViewMixin:
	"""Mixin class for handling view attribute.
	
	<!ENTITY % I_View " view  (All | 
			  Administrator | 
			  AdminAuthority | 
			  Assessor | 
			  Author | 
			  Candidate | 
			  InvigilatorProctor | 
			  Psychometrician | 
			  Scorer | 
			  Tutor )  'All'">
	
	V2_VIEWMAP attribute maps lower-cased view names from v1.2 onto corresponding v2 view values.
	"""
	XMLATTR_view='view'

	V2_VIEWMAP={
		'administrator':'proctor',
		'adminauthority':'proctor',
		'assessor':'scorer',
		'author':'author',
		'candidate':'candidate',
		'invigilator':'proctor',
		'proctor':'proctor',
		'invigilatorproctor':'proctor',
		'psychometrician':'testConstructor',
		'tutor':'tutor',
		'scorer':'scorer'}
		
	V2_VIEWALL='author candidate proctor scorer testConstructor tutor'

	def __init__(self):
		self.view='All'

	
"""...
<!ENTITY % I_FeedbackSwitch " feedbackswitch  (Yes | No )  'Yes'">

<!ENTITY % I_HintSwitch " hintswitch  (Yes | No )  'Yes'">

<!ENTITY % I_SolutionSwitch " solutionswitch  (Yes | No )  'Yes'">
"""

class QTIRCardinality:
	"""rcardinality enumeration::
	
	<!ENTITY % I_Rcardinality " rcardinality  (Single | Multiple | Ordered )  'Single'">
	"""
	decode={
		'Single':1,
		'Multiple':2,
		'Ordered':3
		}
	
	MigrateV2={
		1:qtiv2.QTICardinality.single,
		2:qtiv2.QTICardinality.multiple,
		3:qtiv2.QTICardinality.ordered
		}
		
xsi.MakeEnumeration(QTIRCardinality)

def DecodeRCardinality(value):
	"""Decodes an rcardinality value from a string."""
	try:
		value=value.strip()
		value=value[0].upper()+value[1:].lower()
		return QTIRCardinality.decode[value]
	except KeyError:
		raise ValueError("Can't decode rcardinality from %s"%value)

def EncodeRCardinality(value):
	return QTIRCardinality.encode.get(value,'Single')



"""
<!ENTITY % I_Rtiming " rtiming  (Yes | No )  'No'">

<!ENTITY % I_Uri " uri CDATA  #IMPLIED">
"""

class QTIPositionMixin:
	"""Mixin to define the positional attributes.
	
	<!ENTITY % I_X0 " x0 CDATA  #IMPLIED">
	
	<!ENTITY % I_Y0 " y0 CDATA  #IMPLIED">
	
	<!ENTITY % I_Height " height CDATA  #IMPLIED">
	
	<!ENTITY % I_Width " width CDATA  #IMPLIED">
	"""
	XMLATTR_height=('height',ParseInteger,FormatInteger)
	XMLATTR_width=('width',ParseInteger,FormatInteger)
	XMLATTR_x0=('x0',ParseInteger,FormatInteger)
	XMLATTR_y0=('y0',ParseInteger,FormatInteger)
	
	def __init__(self):
		self.x0=None
		self.y0=None
		self.width=None
		self.height=None

	def GotPosition(self):
		return self.x0 is not None or self.y0 is not None or self.width is not None or self.height is not None
		

"""...

<!ENTITY % I_Embedded " embedded CDATA  'base64'">
"""

class QTILinkRefIdMixin:
	"""Mixin class for handling linkrefid attribute::
	
	<!ENTITY % I_LinkRefId " linkrefid CDATA  #REQUIRED">
	"""
	XMLATTR_linkrefid='linkRefID'

	def __init__(self):
		self.linkRefID=None

"""
...
<!ENTITY % I_VarName " varname CDATA  'SCORE'">

<!ENTITY % I_RespIdent " respident CDATA  #REQUIRED">

<!ENTITY % I_Continue " continue  (Yes | No )  'No'">

<!ENTITY % I_CharSet " charset CDATA  'ascii-us'">

<!ENTITY % I_ScoreModel " scoremodel CDATA  #IMPLIED">

<!ENTITY % I_MinNumber " minnumber CDATA  #IMPLIED">

<!ENTITY % I_MaxNumber " maxnumber CDATA  #IMPLIED">
"""

class QTIFeedbackStyle:
	"""feedbackstyle enumeration::
	
	<!ENTITY % I_FeedbackStyle " feedbackstyle  (Complete | Incremental | Multilevel | Proprietary )  'Complete'">
	"""
	decode={
		'Complete':1,
		'Incremental':2,
		'Multilevel':3,
		'Proprietary':4
		}		
xsi.MakeEnumeration(QTIFeedbackStyle)

def DecodeFeedbackStyle(value):
	"""Decodes a feedbackstyle value from a string."""
	try:
		value=value.strip()
		value=value[0].upper()+value[1:].lower()
		return QTIFeedbackStyle.decode[value]
	except KeyError:
		raise ValueError("Can't decode feedbackstyle from %s"%value)

def EncodeFeedbackStyle(value):
	return QTIFeedbackStyle.encode.get(value,'Complete')


"""
<!ENTITY % I_Case " case  (Yes | No )  'No'">

<!ENTITY % I_EntityRef " entityref ENTITY  #IMPLIED">

<!ENTITY % I_Index " index CDATA  #IMPLIED">
"""
		
class QTIMetadataContainer(QTIElement):
	"""An abstract class used to hold dictionaries of metadata.
	
	There is a single dictionary maintained to hold all metadata values, each
	value is a list of tuples of the form (value string, defining element).
	Values are keyed on the field label or tag name with any leading qmd\_ prefix
	removed."""
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		self.metadata={}

	def DeclareMetadata(self,label,entry,definition=None):
		label=label.lower()
		if label[:4]=="qmd_":
			label=label[4:]
		if not self.metadata.has_key(label):
			self.metadata[label]=[]
		self.metadata[label].append((entry,definition))


class QMDMetadataElement(QTIElement):
	"""Abstract class to represent old-style qmd\_ tags"""
	
	def ContentChanged(self):
		self.DeclareMetadata(self.GetXMLName(),self.GetValue(),self)

class QMDAuthor(QMDMetadataElement):
	"""Not defined by QTI but seems to be in common use."""
	XMLNAME='qmd_author'

class QMDComputerScored(QMDMetadataElement):
	XMLNAME='qmd_computerscored'
	
class QMDDescription(QMDMetadataElement):
	"""Not defined by QTI but seems to be in common use."""
	XMLNAME='qmd_description'
	
class QMDDomain(QMDMetadataElement):
	"""Not defined by QTI but seems to be in common use."""
	XMLNAME='qmd_domain'

class QMDFeedbackPermitted(QMDMetadataElement):
	XMLNAME='qmd_feedbackpermitted'
	
class QMDHintsPermitted(QMDMetadataElement):
	XMLNAME='qmd_hintspermitted'

class QMDItemType(QMDMetadataElement):
	XMLNAME='qmd_itemtype'

class QMDKeywords(QMDMetadataElement):
	"""Not defined by QTI but seems to be in common use."""
	XMLNAME='qmd_keywords'

class QMDMaximumScore(QMDMetadataElement):
	XMLNAME='qmd_maximumscore'

class QMDOrganization(QMDMetadataElement):
	"""Not defined by QTI but seems to be in common use."""
	XMLNAME='qmd_organization'

class QMDRenderingType(QMDMetadataElement):
	XMLNAME='qmd_renderingtype'

class QMDResponseType(QMDMetadataElement):
	XMLNAME='qmd_responsetype'

class QMDScoringPermitted(QMDMetadataElement):
	XMLNAME='qmd_scoringpermitted'

class QMDSolutionsPermitted(QMDMetadataElement):
	XMLNAME='qmd_solutionspermitted'

QMDStatusSourceMap={
	'draft':imsmd.LOM_SOURCE,
	'final':imsmd.LOM_SOURCE,
	'revised':imsmd.LOM_SOURCE,
	'unavailable':imsmd.LOM_SOURCE,
	'experimental':QTI_SOURCE,
	'normal':QTI_SOURCE,
	'retired':QTI_SOURCE
	}

class QMDStatus(QMDMetadataElement):
	XMLNAME='qmd_status'

class QMDTimeDependence(QMDMetadataElement):
	XMLNAME='qmd_timedependence'

class QMDTimeLimit(QMDMetadataElement):
	XMLNAME='qmd_timelimit'

class QMDTitle(QMDMetadataElement):
	"""Not defined by QTI but seems to be in common use."""
	XMLNAME='qmd_title'

class QMDToolVendor(QMDMetadataElement):
	XMLNAME='qmd_toolvendor'
		
class QMDTopic(QMDMetadataElement):
	XMLNAME='qmd_topic'

class QMDMaterial(QMDMetadataElement):
	XMLNAME='qmd_material'

class QMDTypeOfSolution(QMDMetadataElement):
	XMLNAME='qmd_typeofsolution'

class QMDLevelOfDifficulty(QMDMetadataElement):
	"""Represents the level of difficulty element.
	
::

	<!ELEMENT qmd_levelofdifficulty (#PCDATA)>
	"""	
	XMLNAME='qmd_levelofdifficulty'

	LOMDifficultyMap={
		"very easy":1,
		"easy":1,
		"medium":1,
		"difficult":1,
		"very difficult":1
		}
	
	LOMContextMap={
		"pre-school":("pre-school",False), # value is outside LOM defined vocab
		"school":("school",True),
		"he/fe":("higher education",True),
		"vocational":("vocational",False), # value is outside LOM defined vocab
		"professional development":("training",True)
		}


class QMDWeighting(QMDMetadataElement):
	XMLNAME='qmd_weighting'

class QTIMetadata(QTIElement):
	"""
::

	<!ELEMENT qtimetadata (vocabulary? , qtimetadatafield+)>
	"""
	XMLNAME='qtimetadata'
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		self.QTIVocabulary=None
		self.QTIMetadataField=[]
	
	def GetChildren(self):
		children=[]
		xml.OptionalAppend(children,self.QTIVocabulary)
		return children+self.QTIMetadataField


class QTIVocabulary(QTIElement):
	"""
::

	<!ELEMENT vocabulary (#PCDATA)>

	<!ATTLIST vocabulary  %I_Uri;
		%I_EntityRef;
		vocab_type  CDATA  #IMPLIED >
	"""
	XMLNAME="vocabulary"
	XMLATTR_entityref='entityRef'
	XMLATTR_uri='uri'		
	XMLATTR_vocab_type='vocabType'

	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		self.uri=None
		self.entityRef=None
		self.vocabType=None		


class QTIMetadataField(QTIElement):
	"""
::

	<!ELEMENT qtimetadatafield (fieldlabel , fieldentry)>

	<!ATTLIST qtimetadatafield  xml:lang CDATA  #IMPLIED >
	"""
	XMLNAME='qtimetadatafield'
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		self.QTIFieldLabel=QTIFieldLabel(self)
		self.QTIFieldEntry=QTIFieldEntry(self)
	
	def GetChildren(self):
		return [self.QTIFieldLabel,self.QTIFieldEntry]
	
	def ContentChanged(self):
		label=self.QTIFieldLabel.GetValue()
		label={'marks':'maximumscore',
			'qmd_marks':'maximumscore',
			'name':'title',
			'qmd_name':'title',
			'syllabusarea':'topic',
			'qmd_syllabusarea':'topic',
			'item type':'itemtype',
			'question type':'itemtype',
			'qmd_layoutstatus':'status',
			'layoutstatus':'status'}.get(label,label)
		# Still need to handle creator and owner	
		self.DeclareMetadata(label,self.QTIFieldEntry.GetValue(),self)

class QTIFieldLabel(QTIElement):
	XMLNAME="fieldlabel"

class QTIFieldEntry(QTIElement):
	XMLNAME="fieldentry"


#
#	COMMON OBJECT DEFINITIONS
#
class QTIComment(QTIElement):
	"""Represents the qticomment element.
	
::

	<!ELEMENT qticomment (#PCDATA)>
	
	<!ATTLIST qticomment  xml:lang CDATA  #IMPLIED >"""
	XMLNAME='qticomment'
	XMLCONTENT=xml.XMLMixedContent
	

class QTIContentMixin:
	"""Mixin class for handling content-containing elements.
	
	This class is used by all elements that behave as content, the default
	implementation provides an additional contentChildren member that should
	be used to collect any content-like children."""

	def __init__(self):
		self.contentChildren=[]
	
	def IsInline(self):
		"""True if this element can be inlined, False if it is block level
		
		The default implementation return True if all children can be inlined."""
		return self.InlineChildren()
		
	def InlineChildren(self):
		"""True if this element's children can all be inlined."""
		for child in self.contentChildren:
			if not child.IsInline():
				return False
		return True

	def ExtractText(self):
		"""Returns text,lang representing this object."""
		result=[]
		lang=self.GetLang()
		for child in self.contentChildren:
			childText,childLang=child.ExtractText()
			if lang is None:
				lang=childLang
			if childText:
				result.append(childText.strip())
		return string.join(result,' '),lang
	
	def MigrateV2Content(self,parent,childType,log,children=None):
		"""Migrates any contentChildren to v2 adding them to the parent content node.
		
		childType indicates the expected type of children and is one of the html mixin
		classes: InlineMixin, BlockMixin or FlowMixin (=InlineMixin+BlockMixin)."""
		if children is None:
			children=self.contentChildren
		if childType is html.InlineMixin or (childType is html.FlowMixin and self.InlineChildren()):
			# We can only hold inline children, raise an error if find anything else
			brBefore=brAfter=False
			firstItem=True
			for child in children:
				if isinstance(child,(QTIFlow,QTIFlowMat,QTIFlowLabel)):
					brBefore=not firstItem
					brAfter=True
				elif brAfter:
					# we only honour brAfter if flow is followed by something other than flow
					parent.ChildElement(html.Br,(qtiv2.IMSQTI_NAMESPACE,'br'))
					brAfter=False				
				if brBefore:
					parent.ChildElement(html.Br,(qtiv2.IMSQTI_NAMESPACE,'br'))
					brBefore=False
				# we force InlineMixin here to prevent unnecessary checks on inline status
				child.MigrateV2Content(parent,html.InlineMixin,log)
				firstItem=False
		else:
			# childType is html.BlockMixin or html.FlowMixin and we have a mixture of inline/block children
			p=None
			brBefore=False
			brAfter=False
			for child in children:
				try:
					if child.IsInline():
						if brAfter:
							p.ChildElement(html.Br,(qtiv2.IMSQTI_NAMESPACE,'br'))
							brAfter=False
						if isinstance(child,(QTIFlow,QTIFlowMat,QTIFlowLabel)):
							brBefore=brAfter=True
						if p is None:
							p=parent.ChildElement(html.P,(qtiv2.IMSQTI_NAMESPACE,'p'))
							brBefore=False
						if brBefore:
							p.ChildElement(html.Br)
							brBefore=False
						child.MigrateV2Content(p,html.InlineMixin,log)
					else:
						# stop collecting inlines
						p=None
						brBefore=brAfter=False
						child.MigrateV2Content(parent,html.BlockMixin,log)
				except AttributeError:
					raise QTIError("Error: unsupported QTI v1 content element "+child.xmlname)

# 	def MigrateV2ContentMixture(self,mixedupChildren,parent,log):
# 		p=None
# 		brBefore=False
# 		brAfter=False
# 		for child in mixedupChildren:
# 			try:
# 				if child.IsInline():
# 					if brAfter:
# 						parent.ChildElement(html.Br,(qtiv2.IMSQTI_NAMESPACE,'br'))
# 						brAfter=False
# 					if isinstance(child,(QTIFlow,QTIFlowMat,QTIFlowLabel)):
# 						brBefore=brAfter=True
# 					if p is None:
# 						p=parent.ChildElement(html.P,(qtiv2.IMSQTI_NAMESPACE,'p'))
# 						brBefore=False
# 					if brBefore:
# 						parent.ChildElement(html.Br)
# 						brBefore=False
# 					child.MigrateV2Content(p,html.InlineMixin,log)
# 				else:
# 					# stop collecting inlines
# 					p=None
# 					brBefore=brAfter=False
# 					child.MigrateV2Content(parent,html.BlockMixin,log)
# 			except AttributeError:
# 				log.append("Error: unsupported content element "+child.xmlname)
# 				#print "Error: unsupported content element "+child.xmlname
# 				raise
# 				p=None
# 				continue


class QTIFlowMatContainer(QTICommentElement,QTIContentMixin):
	"""Abstract class used to represent objects that contain flow_mat
	
::

	<!ELEMENT XXXXXXXXXX (qticomment? , (material+ | flow_mat+))>
	"""
	def __init__(self,parent):
		QTICommentElement.__init__(self,parent)
		QTIContentMixin.__init__(self)

	def GetChildren(self):
		children=QTICommentElement.GetChildren(self)+self.contentChildren
		return children

	def QTIMaterial(self):
		child=QTIMaterial(self)
		self.contentChildren.append(child)
		return child
	
	def QTIFlowMat(self):
		child=QTIFlowMat(self)
		self.contentChildren.append(child)
		return child
				

class QTIFlowContainer(QTICommentElement,QTIContentMixin):
	"""Abstract class used to represent objects that contain flow and friends
	
::

	<!ELEMENT XXXXXXXXXX (qticomment? , (material | flow | response_*)* )>
	"""
	def __init__(self,parent):
		QTICommentElement.__init__(self,parent)
		QTIContentMixin.__init__(self)

	def GetChildren(self):
		children=QTICommentElement.GetChildren(self)+self.contentChildren
		return children

	def QTIMaterial(self):
		child=QTIMaterial(self)
		self.contentChildren.append(child)
		return child
	
	def QTIFlow(self):
		child=QTIFlow(self)
		self.contentChildren.append(child)
		return child
	
	def QTIResponseThing(self,childClass):
		child=childClass(self)
		self.contentChildren.append(child)
		return child


class QTIMaterial(QTICommentElement,QTIContentMixin):
	"""Represents the material element
	
::

	<!ELEMENT material (qticomment? , (mattext | matemtext | matimage | mataudio | matvideo | matapplet | matapplication | matref | matbreak | mat_extension)+ , altmaterial*)>
	
	<!ATTLIST material  %I_Label;
						xml:lang CDATA  #IMPLIED >
	"""
	XMLNAME='material'
	XMLATTR_label='label'
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTICommentElement.__init__(self,parent)
		QTIContentMixin.__init__(self)
		self.label=None
	
	def GetChildren(self):
		children=QTICommentElement.GetChildren(self)+self.contentChildren
		return children
	
	def QTIMatThingMixin(self,childClass):
		child=childClass(self)
		self.contentChildren.append(child)
		return child
		

class QTIMatThingMixin(QTIContentMixin):
	"""An abstract class used to help identify the mat* elements."""
	pass

class QTIMatText(QTIElement,QTIPositionMixin,QTIMatThingMixin):
	"""Represents the mattext element

::

	<!ELEMENT mattext (#PCDATA)>
	
	<!ATTLIST mattext  texttype    CDATA  'text/plain'
						%I_Label;
						%I_CharSet;
						%I_Uri;
						xml:space    (preserve | default )  'default'
						xml:lang    CDATA  #IMPLIED
						%I_EntityRef;
						%I_Width;
						%I_Height;
						%I_Y0;
						%I_X0; >	
	"""
	XMLNAME='mattext'
	XMLATTR_label='label'
	XMLATTR_charset='charset'
	XMLATTR_uri=('uri',html.DecodeURI,html.EncodeURI)
	XMLATTR_texttype='texttype'				
	XMLCONTENT=xml.XMLMixedContent
	
	SymbolCharsets={
		'greek':1,
		'symbol':1
		}
		
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		QTIPositionMixin.__init__(self)
		QTIMatThingMixin.__init__(self)
		self.label=None
		self.charset='ascii-us'
		self.uri=None
		self.texttype='text/plain'
		self.matChildren=[]
				
	def ContentChanged(self):
		if self.label:
			doc=self.GetDocument()
			if doc:
				doc.RegisterMatThing(self)
		if self.texttype=='text/html':
			if self.uri:
				# The content is external, load it up
				uri=self.ResolveURI(self.uri)
				e=xml.XMLEntity(uri)
			else:
				uri=self.ResolveBase()
				try:
					value=self.GetValue()
				except xml.XMLMixedContentError:
					# Assume that the element content was not protected by CDATA
					children=self.GetChildren()
					value=[]
					for child in children:
						value.append(unicode(child))
					value=string.join(value,'')
				if value:
					e=xml.XMLEntity(value)
			doc=html.XHTMLDocument(baseURI=uri)
			doc.ReadFromEntity(e)
			self.matChildren=doc.root.Body.GetChildren()
			if len(self.matChildren)==1 and isinstance(self.matChildren[0],html.Div):
				div=self.matChildren[0]
				if div.styleClass is None:
					# a single div with no style class is removed...
					self.matChildren=div.GetChildren()
		elif self.texttype=='text/rtf':
			# parse the RTF content
			raise QTIUnimplementedError

	def IsInline(self):
		if self.texttype=='text/plain':
			return True
		elif self.texttype=='text/html':
			# we are inline if all elements in matChildren are inline
			for child in self.matChildren:
				if type(child) in StringTypes or issubclass(child.__class__,html.InlineMixin):
					continue
				else:
					return False
			return True
		else:
			raise QTIUnimplementedError(self.texttype)
			
	def ExtractText(self):
		if self.matChildren:
			# we need to extract the text from these children
			results=[]
			para=[]
			for child in self.matChildren:
				if type(child) in StringTypes:
					para.append(child)
				elif issubclass(child.__class__,html.InlineMixin):
					para.append(child.RenderText())
				else:
					if para:
						results.append(string.join(para,''))
						para=[]
					results.append(child.RenderText())
			if para:
				results.append(string.join(para,''))
			return string.join(results,'\n\n'),self.ResolveLang()
		else:
			return self.GetValue(),self.ResolveLang()

	def MigrateV2Content(self,parent,childType,log):
		if self.texttype=='text/plain':
			data=self.GetValue(True)
			if QTIMatText.SymbolCharsets.has_key(self.charset.lower()):
				# this data is in the symbol font, translate it
				# Note that the first page of unicode is the same as iso-8859-1
				data=data.encode('iso-8859-1').decode('apple-symbol')				
			lang=self.GetLang()
			if lang or self.label:
				if childType is html.BlockMixin:
					span=parent.ChildElement(html.P,(qtiv2.IMSQTI_NAMESPACE,'p'))
				else:
					span=parent.ChildElement(html.Span,(qtiv2.IMSQTI_NAMESPACE,'span'))
				if lang:
					span.SetLang(lang)
				if self.label:
					#span.label=self.label
					span.SetAttribute('label',self.label)
				# force child elements to render as inline XML
				span.AddData(data)
			elif childType is html.BlockMixin:
				p=parent.ChildElement(html.P,(qtiv2.IMSQTI_NAMESPACE,'p'))
				p.AddData(data)
			else:
				# inline or flow, just add the text directly...
				parent.AddData(data)
		elif self.texttype=='text/html':		
			if childType is html.BlockMixin or (childType is html.FlowMixin and not self.IsInline()):
				# Block or mixed-up flow, wrap all text and inline elements in p
				p=None
				for child in self.matChildren:
					if type(child) in StringTypes or issubclass(child.__class__,html.InlineMixin):
						if p is None:
							p=parent.ChildElement(html.P,(qtiv2.IMSQTI_NAMESPACE,'p'))
						if type(child) in StringTypes:
							p.AddData(child)
						else:
							newChild=child.Copy(p)
							qtiv2.FixHTMLNamespace(newChild)															
					else:
						# stop collecting inlines
						p=None
						newChild=child.Copy(parent)
						qtiv2.FixHTMLNamespace(newChild)															
			else:
				# Flow context (with only inline children) or inline context
				for child in self.matChildren:
					if type(child) in StringTypes:
						parent.AddData(child)
					else:
						newChild=child.Copy(parent)
						qtiv2.FixHTMLNamespace(newChild)
		else:
			raise QTIUnimplementedError


class QTIMatEmText(QTIMatText):
	"""Represents matemtext element.
	
::

	<!ELEMENT matemtext (#PCDATA)>
	
	<!ATTLIST matemtext  texttype    CDATA  'text/plain'
						  %I_Label;
						  %I_CharSet;
						  %I_Uri;
						  xml:space    (preserve | default )  'default'
						  xml:lang    CDATA  #IMPLIED
						  %I_EntityRef;
						  %I_Width;
						  %I_Height;
						  %I_Y0;
						  %I_X0; >
	"""
	XMLNAME="matemtext"
	XMLCONTENT=xml.XMLMixedContent
	

class QTIMatImage(QTIElement,QTIPositionMixin,QTIMatThingMixin):
	"""Represents matimage element.
	
::

	<!ELEMENT matimage (#PCDATA)>
	
	<!ATTLIST matimage  imagtype    CDATA  'image/jpeg'
						 %I_Label;
						 %I_Height;
						 %I_Uri;
						 %I_Embedded;
						 %I_Width;
						 %I_Y0;
						 %I_X0;
						 %I_EntityRef; >
	"""
	XMLNAME="matimage"
	XMLATTR_imagtype='imageType'
	XMLATTR_label='label'
	XMLATTR_uri=('uri',html.DecodeURI,html.EncodeURI)
	XMLCONTENT=xml.XMLMixedContent
	
	
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		QTIPositionMixin.__init__(self)
		QTIMatThingMixin.__init__(self)
		self.imageType='image/jpeg'
		self.label=None
		self.uri=None
				
	def IsInline(self):
		return True
			
	def ExtractText(self):
		"""We cannot extract text from matimage so we return a simple string."""
		return "[image]"

	def MigrateV2Content(self,parent,childType,log):
		if self.uri is None:
			raise QTIUnimplementedError("inclusion of inline images")
		if childType is html.BlockMixin:
			# We must wrap this img in a <p>
			p=parent.ChildElement(html.P,(qtiv2.IMSQTI_NAMESPACE,'p'))
			img=p.ChildElement(html.Img,(qtiv2.IMSQTI_NAMESPACE,'img'))
		else:
			img=parent.ChildElement(html.Img,(qtiv2.IMSQTI_NAMESPACE,'img'))
		img.src=self.ResolveURI(self.uri)
		if self.width is not None:
			img.width=html.LengthType(self.width)
		if self.height is not None:
			img.height=html.LengthType(self.height)
	

class QTIMatAudio(QTIElement,QTIMatThingMixin):
	"""Represents mataudio element.
	
::

	<!ELEMENT mataudio (#PCDATA)>
	
	<!ATTLIST mataudio  audiotype   CDATA  'audio/base'
						 %I_Label;
						 %I_Uri;
						 %I_Embedded;
						 %I_EntityRef; >
	"""
	XMLNAME="mataudio"
	XMLCONTENT=xml.XMLMixedContent

	XMLATTR_audiotype='audioType'
	XMLATTR_label='label'
	XMLATTR_uri=('uri',html.DecodeURI,html.EncodeURI)
	XMLCONTENT=xml.XMLMixedContent
	
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		QTIMatThingMixin.__init__(self)
		self.audioType='audio/base'
		self.label=None
		self.uri=None
				
	def IsInline(self):
		return True
			
	def ExtractText(self):
		"""We cannot extract text from mataudio so we return a simple string."""
		return "[sound]"

	def MigrateV2Content(self,parent,childType,log):
		if self.uri is None:
			raise QTIUnimplementedError("inclusion of inline audio")
		if childType is html.BlockMixin:
			# We must wrap this object in a <p>
			p=parent.ChildElement(html.P,(qtiv2.IMSQTI_NAMESPACE,'p'))
			obj=p.ChildElement(html.Object,(qtiv2.IMSQTI_NAMESPACE,'object'))
		else:
			obj=parent.ChildElement(html.Object,(qtiv2.IMSQTI_NAMESPACE,'object'))		
		obj.data=self.ResolveURI(self.uri)
		obj.type=self.audioType


class QTIMatVideo(QTIElement):
	"""Represents mataudio element.
	
::

	<!ELEMENT matvideo (#PCDATA)>
	
	<!ATTLIST matvideo  videotype   CDATA  'video/avi'
						 %I_Label;
						 %I_Uri;
						 %I_Width;
						 %I_Height;
						 %I_Y0;
						 %I_X0;
						 %I_Embedded;
						 %I_EntityRef; >
	"""
	XMLNAME="matvideo"
	XMLCONTENT=xml.XMLMixedContent


class QTIMatApplet(QTIElement):
	"""Represents matapplet element.
	
::

	<!ELEMENT matapplet (#PCDATA)>
	
	<!ATTLIST matapplet  %I_Label;
						  %I_Uri;
						  %I_Y0;
						  %I_Height;
						  %I_Width;
						  %I_X0;
						  %I_Embedded;
						  %I_EntityRef; >
	"""
	XMLNAME="matapplet"
	XMLCONTENT=xml.XMLMixedContent


class QTIMatApplication(QTIElement):
	"""Represents matapplication element.
	
::

	<!ELEMENT matapplication (#PCDATA)>
	
	<!ATTLIST matapplication  apptype     CDATA  #IMPLIED
							   %I_Label;
							   %I_Uri;
							   %I_Embedded;
							   %I_EntityRef; >
	"""
	XMLNAME="matapplication"
	XMLCONTENT=xml.XMLMixedContent


class QTIMatBreak(QTIElement,QTIMatThingMixin):
	"""Represents matbreak element.
	
::

	<!ELEMENT matbreak EMPTY>
	"""
	XMLNAME="matbreak"
	XMLCONTENT=xml.XMLEmpty
	
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		QTIMatThingMixin.__init__(self)
				
	def IsInline(self):
		return True
			
	def ExtractText(self):
		"""Returns a simple line break"""
		return "\n"

	def MigrateV2Content(self,parent,childType,log):
		if childType in (html.InlineMixin,html.FlowMixin):
			parent.ChildElement(html.Br,(qtiv2.IMSQTI_NAMESPACE,'br'))
		else:
			# a break in a group of block level elements is ignored
			pass			
	
	
class QTIMatRef(QTIMatThingMixin,QTIElement):
	"""Represents matref element::

	<!ELEMENT matref EMPTY>
	
	<!ATTLIST matref  %I_LinkRefId; >
	"""
	XMLNAME="matref"
	XMLATTR_linkrefid='linkRefID'
	XMLCONTENT=xml.XMLEmpty

	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		QTIMatThingMixin.__init__(self)

	def FindMatThing(self):
		doc=self.GetDocument()
		if doc:
			return doc.FindMatThing(self.linkRefID)
		else:
			raise QTIError("Bad matref: %s"%str(self.linkRefID))

	def IsInline(self):
		return self.FindMatThing().IsInline()
	
	def ExtractText(self):
		return self.FindMatThing().ExtractText()
	
	def MigrateV2Content(self,parent,childType,log):
		self.FindMatThing().MigrateV2Content(parent,childType,log)

		
class QTIMaterialRef(QTIElement):
	"""Represents material_ref element.
	
::

	<!ELEMENT material_ref EMPTY>
	
	<!ATTLIST material_ref  %I_LinkRefId; >
	"""
	XMLNAME="material_ref"
	XMLCONTENT=xml.XMLEmpty


class QTIAltMaterial(QTICommentElement):
	"""Represents the altmaterial element.

::

	<!ELEMENT altmaterial (qticomment? ,
		(mattext | matemtext | matimage | mataudio | matvideo |
		matapplet | matapplication | matref | matbreak | mat_extension)+)>
	
	<!ATTLIST altmaterial  xml:lang CDATA  #IMPLIED >
	"""
	XMLNAME="material_ref"
	XMLCONTENT=xml.XMLElementContent
	
class QTIVarType:
	"""vartype enumeration."""
	decode={
		'Integer':1,
		'String':2,
		'Decimal':3,
		'Scientific':4,
		'Boolean':5,
		'Enumerated':5,
		'Set':6
		}
xsi.MakeEnumeration(QTIVarType)

def DecodeVarType(value):
	try:
		return QTIVarType.decode[value]
	except KeyError:
		if value:
			try:
				value=value[0].upper()+value[1:].lower()
				return QTIVarType.decode[value]
			except KeyError:
				pass
		return 0

def EncodeVarType(value):
	if value:
		return QTIVarType.encode[value]
	else:
		return ''
		

class QTIDecVar(QTIElement):
	"""Represents the decvar element
	
::

	<!ELEMENT decvar (#PCDATA)>
	
	<!ATTLIST decvar  %I_VarName;
					   vartype     (Integer | 
									String | 
									Decimal | 
									Scientific | 
									Boolean | 
									Enumerated | 
									Set )  'Integer'
					   defaultval CDATA  #IMPLIED
					   minvalue   CDATA  #IMPLIED
					   maxvalue   CDATA  #IMPLIED
					   members    CDATA  #IMPLIED
					   cutvalue   CDATA  #IMPLIED >
	"""
	XMLNAME="decvar"
	XMLATTR_cutvalue='cutValue'
	XMLATTR_defaultval='defaultValue'	
	XMLATTR_maxvalue='maxValue'
	XMLATTR_members='members'
	XMLATTR_minvalue='minValue'
	XMLATTR_varname='varName'
	XMLATTR_vartype=('varType',DecodeVarType,EncodeVarType)
	XMLCONTENT=xml.XMLMixedContent
	
	V2TYPEMAP={
		QTIVarType.Integer:qtiv2.BaseType.integer,
		QTIVarType.String:qtiv2.BaseType.string,
		QTIVarType.Decimal:qtiv2.BaseType.float,
		QTIVarType.Scientific:qtiv2.BaseType.float,
		QTIVarType.Boolean:qtiv2.BaseType.boolean,
		QTIVarType.Enumerated:qtiv2.BaseType.identifier,
		QTIVarType.Set:qtiv2.BaseType.identifier
		}
		
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		self.varName='SCORE'
		self.varType=QTIVarType.Integer
		self.defaultValue=None
		self.minValue=None
		self.maxValue=None
		self.members=None
		self.cutValue=None
			
	def MigrateV2(self,v2Item,log):
		d=v2Item.ChildElement(qtiv2.QTIOutcomeDeclaration)
		v2Type=QTIDecVar.V2TYPEMAP.get(self.varType,None)
		if self.varType==QTIVarType.Set:
			log.append('Warning: treating vartype="Set" as equivalent to "Enumerated"')
		elif v2Type is None:
			log.append('Error: bad vartype for decvar "%s"; defaulting to integer'%self.varName)
			v2Type=qtiv2.BaseType.integer
		d.baseType=v2Type
		d.cardinality=qtiv2.QTICardinality.single
		d.identifier=qtiv2.ValidateIdentifier(self.varName)
		if self.defaultValue is not None:
			value=d.ChildElement(qtiv2.QTIDefaultValue).ChildElement(qtiv2.QTIValue)
			value.SetValue(self.defaultValue)
		# to do... min and max were actually constraints in QTI v1 ...
		# so we will need to fix these up later with responseConditions to constraint the value
		if self.minValue is not None:
			d.normalMinimum=float(self.minValue)
		if self.maxValue is not None:
			d.normalMaximum=float(self.maxValue)
		if self.members is not None:
			log.append('Warning: enumerated members no longer supported, ignoring "%s"'%self.members)
		if v2Type in (qtiv2.BaseType.integer,qtiv2.BaseType.float):
			# we need to adjust minValue/maxValue later
			if self.cutValue is not None:
				d.masteryValue=float(self.cutValue)
		v2Item.RegisterDeclaration(d)

	def ContentChanged(self):
		"""The decvar element is supposed to be empty but QTI v1 content is all over the place."""
		try:
			value=self.GetValue()
			if value is not None:
				assert value.strip()==''
		except xml.XMLMixedContentError:
			# Even more confusing
			pass


class QTISetVarAction:
	"""action enumeration."""
	decode={
		'Set':1,
		'Add':2,
		'Subtract':3,
		'Multiply':4,
		'Divide':5
		}
xsi.MakeEnumeration(QTISetVarAction)

def DecodeSetVarAction(value):
	try:
		return QTISetVarAction.decode[value]
	except KeyError:
		if value:
			try:
				value=value[0].upper()+value[1:].lower()
				return QTISetVarAction.decode[value]
			except KeyError:
				pass
		return 0

def EncodeSetVarAction(value):
	if value:
		return QTISetVarAction.encode[value]
	else:
		return ''


class QTISetVar(QTIElement):
	"""Represents the setvar element.

::

	<!ELEMENT setvar (#PCDATA)>
	
	<!ATTLIST setvar  %I_VarName;
					   action     (Set | Add | Subtract | Multiply | Divide )  'Set' >
	"""
	XMLNAME="setvar"
	XMLATTR_varname='varName'
	XMLATTR_action=('action',DecodeSetVarAction,EncodeSetVarAction)
	XMLCONTENT=xml.XMLMixedContent
	
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		self.varName='SCORE'
		self.action=QTISetVarAction.Set
	
	def MigrateV2Rule(self,parent,log):
		v2Item=parent.GetAssessmentItem()
		identifier=qtiv2.ValidateIdentifier(self.varName)
		outcome=v2Item.declarations.get(identifier,None)
		if outcome is None:
			raise QTIUnimplementedError("Auto-declared outcomes")
		setValue=parent.ChildElement(qtiv2.QTISetOutcomeValue)
		setValue.identifier=identifier
		if outcome.cardinality!=qtiv2.QTICardinality.single:
			raise QTIUnimplementedError("setvar for '%s' with cardinality %s"%(identifier,
				qtiv2.QTICardinality.encode[outcome.cardinality]))
		value=None
		variable=None
		if not self.action or self.action==QTISetVarAction.Set:
			value=setValue.ChildElement(qtiv2.QTIBaseValue)
		else:
			if self.action==QTISetVarAction.Add:
				op=setValue.ChildElement(qtiv2.QTISum)
			elif self.action==QTISetVarAction.Subtract:
				op=setValue.ChildElement(qtiv2.QTISubtract)
			elif self.action==QTISetVarAction.Multiply:
				op=setValue.ChildElement(qtiv2.QTIProduct)
			elif self.action==QTISetVarAction.Divide:
				op=setValue.ChildElement(qtiv2.QTIDivide)
			variable=op.ChildElement(qtiv2.QTIVariable)
			variable.identifier=identifier
			value=op.ChildElement(qtiv2.QTIBaseValue)
		value.baseType=outcome.baseType
		value.SetValue(self.GetValue())
		

class QTIInterpretVar(QTIElement,QTIContentMixin,QTIViewMixin):
	"""Represents the interpretvar element.

::

	<!ELEMENT interpretvar (material | material_ref)>
	
	<!ATTLIST interpretvar  %I_View;
							 %I_VarName; >
	"""
	XMLNAME="interpretvar"
	XMLATTR_view='view'
	XMLATTR_varname='varName'
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		QTIContentMixin.__init__(self)
		QTIViewMixin.__init__(self)
		self.varName='SCORE'
	
	def QTIMaterial(self):
		child=QTIMaterial(self)
		self.contentChildren.append(child)
		return child
	
	def QTIMaterialRef(self):
		child=QTIMaterialRef(self)
		self.contentChildren.append(child)
		return child
	
	def MigrateV2(self,v2Item,log):
		identifier=qtiv2.ValidateIdentifier(self.varName)
		if self.view.lower()!='all':
			log.append('Warning: view restriction on outcome interpretation no longer supported (%s)'%self.view)
		d=v2Item.declarations.get(identifier)
		di,lang=self.ExtractText()
		di=xsi.WhiteSpaceCollapse(di)
		if d.interpretation:
			d.interpretation=d.interpretation+"; "+di
		else:
			d.interpretation=di
		# we drop the lang as this isn't supported on declarations
		
		
class QTIConditionVar(QTIElement):
	"""Represents the interpretvar element.

::

	<!ELEMENT conditionvar (not | and | or | unanswered | other | varequal | varlt |
		varlte | vargt | vargte | varsubset | varinside | varsubstring | durequal |
		durlt | durlte | durgt | durgte | var_extension)+>
	
	"""
	XMLNAME="conditionvar"
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		self.ExpressionMixin=[]
	
	def QTIVarExtension(self):
		child=QTIVarExtension(self)
		self.ExpressionMixin.append(child)
		return child
	
	def GetChildren(self):
		return self.ExpressionMixin

	def MigrateV2Expression(self,parent,log):
		if len(self.ExpressionMixin)>1:
			# implicit and
			eAnd=parent.ChildElement(qtiv2.QTIAnd)
			for ie in self.ExpressionMixin:
				ie.MigrateV2Expression(eAnd,log)
		elif self.ExpressionMixin:
			self.ExpressionMixin[0].MigrateV2Expression(parent,log)
		else:
			log.append("Warning: empty condition replaced with null operator")
			parent.ChildElement(qtiv2.QTINull)
		

class ExpressionMixin:
	"""Abstract mixin class to indicate an expression"""
	pass


class QTINot(QTIElement,ExpressionMixin):
	"""Represents the not element.

::

	<!ELEMENT not (and | or | not | unanswered | other | varequal | varlt | varlte |
		vargt | vargte | varsubset | varinside | varsubstring | durequal | durlt |
		durlte | durgt | durgte)>	
	"""
	XMLNAME="not"
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		self.ExpressionMixin=None
	
	def GetChildren(self):
		return self.ExpressionMixin

	def MigrateV2Expression(self,parent,log):
		if self.ExpressionMixin is None:
			log.append("Warning: empty not condition replaced with null operator")
			parent.ChildElement(qtiv2.QTINull)
		else:
			eNot=parent.ChildElement(qtiv2.QTINot)
			self.ExpressionMixin.MigrateV2Expression(eNot,log)


class QTIAnd(QTIElement,ExpressionMixin):
	"""Represents the and element.

::

	<!ELEMENT and (not | and | or | unanswered | other | varequal | varlt | varlte |
		vargt | vargte | varsubset | varinside | varsubstring | durequal | durlt |
		durlte | durgt | durgte)+>	
	"""
	XMLNAME="and"
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		self.ExpressionMixin=[]
	
	def GetChildren(self):
		return self.ExpressionMixin

	def MigrateV2Expression(self,parent,log):
		if len(self.ExpressionMixin):
			eAnd=parent.ChildElement(qtiv2.QTIAnd)
			for e in self.ExpressionMixin:
				e.MigrateV2Expression(eAnd,log)
		else:
			log.append("Warning: empty and condition replaced with null operator")
			parent.ChildElement(qtiv2.QTINull)


class QTIOr(QTIElement,ExpressionMixin):
	"""Represents the or element.

::

	<!ELEMENT or (not | and | or | unanswered | other | varequal | varlt | varlte |
		vargt | vargte | varsubset | varinside | varsubstring | durequal | durlt |
		durlte | durgt | durgte)+>
	"""
	XMLNAME="or"
	XMLCONTENT=xml.XMLElementContent

	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		self.ExpressionMixin=[]
	
	def GetChildren(self):
		return self.ExpressionMixin

	def MigrateV2Expression(self,parent,log):
		if len(self.ExpressionMixin):
			eOr=parent.ChildElement(qtiv2.QTIOr)
			for e in self.ExpressionMixin:
				e.MigrateV2Expression(eOr,log)
		else:
			log.append("Warning: empty or condition replaced with null operator")
			parent.ChildElement(qtiv2.QTINull)
		

class QTIVarThing(QTIElement,ExpressionMixin):
	"""Abstract class for var* elements."""
	XMLATTR_respident='responseIdentifier'
	XMLATTR_index=('index',ParseInteger,FormatInteger)
	XMLCONTENT=xml.XMLMixedContent

	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		self.responseIdentifier=''
		self.index=None

	def MigrateV2Missing(self,identifier,parent,log):
		log.append("Warning: test of undeclared response (%s) replaced with Null operator"%identifier)
		parent.ChildElement(qtiv2.QTINull)
	
	def MigrateV2Variable(self,d,parent,log):
		if self.index:
			if d.cardinality==qtiv2.QTICardinality.multiple:
				log.append("Warning: index ignored for response variable of cardinality multiple")
			elif d.cardinality==qtiv2.QTICardinality.single:
				log.append("Warning: index ignored for response variable of cardinality single")
			else:
				parent=parent.ChildElement(qtiv2.QTIIndex)
				parent.n=self.index
		varExpression=parent.ChildElement(qtiv2.QTIVariable)
		varExpression.identifier=d.identifier
	
	def MigrateV2Value(self,d,parent,log):
		value=self.GetValue().strip()
		if d.baseType in (qtiv2.BaseType.pair,qtiv2.BaseType.directedPair,qtiv2.BaseType.point):
			value=value.replace(',',' ')
		elif d.baseType==qtiv2.BaseType.identifier:
			value=qtiv2.ValidateIdentifier(value)
		bv=parent.ChildElement(qtiv2.QTIBaseValue)
		bv.baseType=d.baseType
		bv.SetValue(value)
		
	
class QTIVarEqual(QTIVarThing):
	"""Represents the varequal element.

::

	<!ELEMENT varequal (#PCDATA)>
	
	<!ATTLIST varequal  %I_Case;
						 %I_RespIdent;
						 %I_Index; >
	"""
	XMLNAME="varequal"
	XMLATTR_case=('case',ParseYesNo,FormatYesNo)

	def __init__(self,parent):
		QTIVarThing.__init__(self,parent)
		self.case=False
	
	def MigrateV2Expression(self,parent,log):
		v2Item=parent.GetAssessmentItem()
		identifier=qtiv2.ValidateIdentifier(self.responseIdentifier)
		d=v2Item.declarations.get(identifier,None)
		if d is None:
			self.MigrateV2Missing(identifier,parent,log)
		elif d.cardinality==qtiv2.QTICardinality.single:
			# simple test of equality
			if d.baseType==qtiv2.BaseType.identifier or d.baseType==qtiv2.BaseType.pair:
				if not self.case:
					log.append("Warning: case-insensitive comparison of identifiers not supported in version 2")
				expression=parent.ChildElement(qtiv2.QTIMatch)
			elif d.baseType==qtiv2.BaseType.integer:
				expression=parent.ChildElement(qtiv2.QTIMatch)
			elif d.baseType==qtiv2.BaseType.string:
				expression=parent.ChildElement(qtiv2.QTIStringMatch)
				expression.caseSensitive=self.case
			elif d.baseType==qtiv2.BaseType.float:
				log.append("Warning: equality operator with float values is deprecated")
				expression=parent.ChildElement(qtiv2.QTIEqual)
			else:
				raise QTIUnimplementedOperator("varequal(%s)"%qtiv2.BaseType.Encode(d.baseType))
			self.MigrateV2Variable(d,expression,log)
			self.MigrateV2Value(d,expression,log)
		else:
			# This test simply becomes a member-test operation
			if d.baseType==qtiv2.BaseType.identifier or qtiv2.BaseType.pair:
				if not self.case:
					log.append("Warning: case-insensitive comparison of identifiers not supported in version 2")
			elif d.baseType==qtiv2.BaseType.string:
				if not self.case:
					log.append("Warning: member operation cannot be case-insensitive when baseType is string")
			elif d.baseType==qtiv2.BaseType.float:
				log.append("Warning: member operation is deprecated when baseType is float")
			else:
				raise QTIUnimplementedOperator("varequal(%s)"%qtiv2.BaseType.Encode(d.baseType))
			expression=parent.ChildElement(qtiv2.QTIMember)
			self.MigrateV2Value(d,expression,log)
			self.MigrateV2Variable(d,expression,log)


class QTIVarInequality(QTIVarThing):
	"""Abstract class for varlt, varlte, vargt and vargte."""

	def MigrateV2Inequality(self):
		"""Returns the class to use in qtiv2"""
		raise QTIUnimplementedOperator(self.xmlname)
		
	def MigrateV2Expression(self,parent,log):
		v2Item=parent.GetAssessmentItem()
		identifier=qtiv2.ValidateIdentifier(self.responseIdentifier)
		d=v2Item.declarations.get(identifier,None)
		if d is None:
			self.MigrateV2Missing(identifier,parent,log)
		elif d.cardinality==qtiv2.QTICardinality.single:
			# simple inequality
			if d.baseType==qtiv2.BaseType.integer or d.baseType==qtiv2.BaseType.float:
				expression=parent.ChildElement(self.MigrateV2Inequality())
			else:
				raise QTIUnimplementedOperator("%s(%s)"%(self.xmlname,qtiv2.BaseType.Encode(d.baseType)))
			self.MigrateV2Variable(d,expression,log)
			self.MigrateV2Value(d,expression,log)
		else:
			raise QTIUnimplementedOperator("%s(%s:%s)"%(self.xmlname,qtiv2.Cardinality.Encode(d.cardinality),qtiv2.BaseType.Encode(d.baseType)))

	
class QTIVarLT(QTIVarInequality):
	"""Represents the varlt element::

	<!ELEMENT varlt (#PCDATA)>
	
	<!ATTLIST varlt  %I_RespIdent;
					  %I_Index; >
	"""
	XMLNAME="varlt"
	XMLCONTENT=xml.XMLMixedContent

	def MigrateV2Inequality(self):
		return qtiv2.LT


class QTIVarLTE(QTIVarInequality):
	"""Represents the varlte element::

	<!ELEMENT varlte (#PCDATA)>
	
	<!ATTLIST varlte  %I_RespIdent;
					   %I_Index; >
	"""
	XMLNAME="varlte"
	XMLCONTENT=xml.XMLMixedContent

	def MigrateV2Inequality(self):
		return qtiv2.LTE


class QTIVarGT(QTIVarInequality):
	"""Represents the vargt element::

	<!ELEMENT vargt (#PCDATA)>
	
	<!ATTLIST vargt  %I_RespIdent;
					  %I_Index; >
	"""
	XMLNAME="vargt"
	XMLCONTENT=xml.XMLMixedContent

	def MigrateV2Inequality(self):
		return qtiv2.GT


class QTIVarGTE(QTIVarInequality):
	"""Represents the vargte element::

	<!ELEMENT vargte (#PCDATA)>
	
	<!ATTLIST vargte  %I_RespIdent;
					   %I_Index; >
	"""
	XMLNAME="vargte"
	XMLCONTENT=xml.XMLMixedContent

	def MigrateV2Inequality(self):
		return qtiv2.GTE


class QTIVarSubset(QTIElement,ExpressionMixin):
	"""Represents the varsubset element.

::

	<!ELEMENT varsubset (#PCDATA)>
	
	<!ATTLIST varsubset  %I_RespIdent;
						  setmatch     (Exact | Partial )  'Exact'
						  %I_Index; >
	"""
	XMLNAME="varsubset"
	XMLCONTENT=xml.XMLMixedContent


class QTIVarInside(QTIVarThing):
	"""Represents the varinside element.

::

	<!ELEMENT varinside (#PCDATA)>
	
	<!ATTLIST varinside  areatype     (Ellipse | Rectangle | Bounded )  #REQUIRED
						  %I_RespIdent;
						  %I_Index; >
	"""
	XMLNAME="varinside"
	XMLATTR_areatype=('areaType',DecodeArea,EncodeArea)
	XMLCONTENT=xml.XMLMixedContent

	def __init__(self,parent):
		QTIVarThing.__init__(self,parent)
		self.areaType=None
	
	def MigrateV2Expression(self,parent,log):
		v2Item=parent.FindParent(qtiv2.QTIAssessmentItem)
		identifier=qtiv2.ValidateIdentifier(self.responseIdentifier)
		d=v2Item.declarations.get(identifier,None)
		if d is None:
			self.MigrateV2Missing(identifier,parent,log)
		elif d.cardinality==qtiv2.QTICardinality.single:
			# is the point in the area?
			if d.baseType==qtiv2.BaseType.point:
				expression=parent.ChildElement(qtiv2.QTIInside)
				expression.shape,coords=MigrateV2AreaCoords(self.areaType,self.GetValue(),log)
				for c in coords:
					expression.coords.values.append(html.LengthType(c))
				self.MigrateV2Variable(d,expression,log)			
			else:
				raise QTIUnimplementedError("varinside(%s)"%qtiv2.EncodeBaseType(d.baseType))
		else:
			raise QTIUnimplementedError("varinside with multiple/orderd variable")


class QTIVarSubString(QTIElement,ExpressionMixin):
	"""Represents the varsubstring element.

::

	<!ELEMENT varsubstring (#PCDATA)>
	
	<!ATTLIST varsubstring  %I_Index;
							 %I_RespIdent;
							 %I_Case; >
	"""
	XMLNAME="varsubstring"
	XMLCONTENT=xml.XMLMixedContent


class QTIDurEqual(QTIElement,ExpressionMixin):
	"""Represents the durequal element.

::

	<!ELEMENT durequal (#PCDATA)>
	
	<!ATTLIST durequal  %I_Index;
						 %I_RespIdent; >
	"""
	XMLNAME="durequal"
	XMLCONTENT=xml.XMLMixedContent


class QTIDurLT(QTIElement,ExpressionMixin):
	"""Represents the durlt element.

::

	<!ELEMENT durlt (#PCDATA)>
	
	<!ATTLIST durlt  %I_Index;
					  %I_RespIdent; >
	"""
	XMLNAME="durlt"
	XMLCONTENT=xml.XMLMixedContent


class QTIDurLTE(QTIElement,ExpressionMixin):
	"""Represents the durlte element.

::

	<!ELEMENT durlte (#PCDATA)>
	
	<!ATTLIST durlte  %I_Index;
					   %I_RespIdent; >
	"""
	XMLNAME="durlte"
	XMLCONTENT=xml.XMLMixedContent


class QTIDurGT(QTIElement,ExpressionMixin):
	"""Represents the durgt element.

::

	<!ELEMENT durgt (#PCDATA)>
	
	<!ATTLIST durgt  %I_Index;
					  %I_RespIdent; >
	"""
	XMLNAME="durgt"
	XMLCONTENT=xml.XMLMixedContent


class QTIDurGTE(QTIElement,ExpressionMixin):
	"""Represents the durgte element.

::

	<!ELEMENT durgte (#PCDATA)>
	
	<!ATTLIST durgte  %I_Index;
					   %I_RespIdent; >
	"""
	XMLNAME="durgte"
	XMLCONTENT=xml.XMLMixedContent


class QTIUnanswered(QTIElement,ExpressionMixin):
	"""Represents the unanswered element.
	
::

	<!ELEMENT unanswered (#PCDATA)>
	
	<!ATTLIST unanswered  %I_RespIdent; >
	"""
	XMLNAME="unanswered"
	XMLCONTENT=xml.XMLMixedContent


class QTIOther(QTIElement,ExpressionMixin):
	"""Represents the other element::

	<!ELEMENT other (#PCDATA)>	
	"""
	XMLNAME="other"
	XMLCONTENT=xml.XMLMixedContent

	def MigrateV2Expression(self,parent,log):
		log.append("Warning: replacing <other/> with the base value true - what did you want me to do??")
		bv=parent.ChildElement(qtiv2.QTIBaseValue)
		bv.baseType=qtiv2.BaseType.boolean
		bv.SetValue('true')


class QTIDuration(QTIElement):
	"""Represents the duration element.
	
::

	<!ELEMENT duration (#PCDATA)>
	"""
	XMLNAME="duration"
	XMLCONTENT=xml.XMLMixedContent


class QTIDisplayFeedback(QTIElement,QTILinkRefIdMixin):
	"""Represents the displayfeedback element.
	
::

	<!ELEMENT displayfeedback (#PCDATA)>
	
	<!ATTLIST displayfeedback  feedbacktype  (Response | Solution | Hint )  'Response'
								%I_LinkRefId; >
	"""
	XMLNAME="displayfeedback"
	XMLATTR_feedbacktype='feedbackType'
	XMLCONTENT=xml.XMLMixedContent

	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		QTILinkRefIdMixin.__init__(self)
		self.feedbackType='Response'
		
	def MigrateV2Rule(self,parent,log):
		v2Item=parent.GetAssessmentItem()
		identifier=qtiv2.ValidateIdentifier(self.linkRefID,'FEEDBACK_')
		outcome=v2Item.declarations.get('FEEDBACK',None)
		if outcome is None:
			d=v2Item.ChildElement(qtiv2.QTIOutcomeDeclaration)
			d.baseType=qtiv2.BaseType.identifier
			d.cardinality=qtiv2.QTICardinality.multiple
			d.identifier='FEEDBACK'
			v2Item.RegisterDeclaration(d)
		setValue=parent.ChildElement(qtiv2.QTISetOutcomeValue)
		setValue.identifier='FEEDBACK'
		multiple=setValue.ChildElement(qtiv2.QTIMultiple)
		variable=multiple.ChildElement(qtiv2.QTIVariable)
		variable.identifier='FEEDBACK'
		value=multiple.ChildElement(qtiv2.QTIBaseValue)
		value.baseType=qtiv2.BaseType.identifier
		value.SetValue(self.linkRefID)
		

class QTIObjectives(QTIFlowMatContainer,QTIViewMixin):
	"""Represents the objectives element
	
::

	<!ELEMENT objectives (qticomment? , (material+ | flow_mat+))>

	<!ATTLIST objectives  %I_View; >"""
	XMLNAME='objectives'
	XMLCONTENT=xml.XMLElementContent
		
	def __init__(self,parent):
		QTIFlowMatContainer.__init__(self,parent)
		QTIViewMixin.__init__(self)
		
	def MigrateV2(self,v2Item,log):
		"""Adds rubric representing these objectives to the given item's body"""
		rubric=v2Item.ChildElement(qtiv2.QTIItemBody).ChildElement(qtiv2.QTIRubricBlock)
		if self.view.lower()=='all':
			rubric.SetAttribute('view',(QTIObjectives.V2_VIEWALL))
		else:
			oldView=self.view.lower()
			view=QTIObjectives.V2_VIEWMAP.get(oldView,'author')
			if view!=oldView:
				log.append("Warning: changing view %s to %s"%(self.view,view))
			rubric.SetAttribute('view',view)
		# rubric is not a flow-container so we force inlines to be p-wrapped
		self.MigrateV2Content(rubric,html.BlockMixin,log)
				
	def LRMMigrateObjectives(self,lom,log):
		"""Adds educational description from these objectives."""
		description,lang=self.ExtractText()
		eduDescription=lom.ChildElement(imsmd.LOMEducational).ChildElement(imsmd.LOMDescription)
		eduDescription.AddString(lang,description)


class QTIRubric(QTIFlowMatContainer,QTIViewMixin):
	"""Represents the rubric element.
	
::

	<!ELEMENT rubric (qticomment? , (material+ | flow_mat+))>
	
	<!ATTLIST rubric  %I_View; >"""
	XMLNAME='rubric'
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIFlowMatContainer.__init__(self,parent)
		QTIViewMixin.__init__(self)
	
	def MigrateV2(self,v2Item,log):
		if self.view.lower()=='all':
			log.append('Warning: rubric with view="All" replaced by <div> with class="rubric"')
			rubric=v2Item.ChildElement(qtiv2.QTIItemBody).ChildElement(html.Div,(qtiv2.IMSQTI_NAMESPACE,'div'))
			rubric.styleClass='rubric'
		else:
			rubric=v2Item.ChildElement(qtiv2.QTIItemBody).ChildElement(qtiv2.QTIRubricBlock)
			oldView=self.view.lower()
			view=QTIObjectives.V2_VIEWMAP.get(oldView,'author')
			if view!=oldView:
				log.append("Warning: changing view %s to %s"%(self.view,view))
			rubric.SetAttribute('view',view)
		# rubric is not a flow-container so we force inlines to be p-wrapped
		self.MigrateV2Content(rubric,html.BlockMixin,log)


class QTIFlowMat(QTIFlowMatContainer):
	"""Represent flow_mat element
	
::

	<!ELEMENT flow_mat (qticomment? , (flow_mat | material | material_ref)+)>
	
	<!ATTLIST flow_mat  %I_Class; >"""
	XMLNAME="flow_mat"
	XMLATTR_class='flowClass'
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIFlowMatContainer.__init__(self,parent)
		self.flowClass=None
		
	def IsInline(self):
		"""flowmat is always treated as a block if flowClass is specified, otherwise
		it is treated as a block unless it is an only child."""
		if self.flowClass is None:
			return self.InlineChildren()
		else:
			return False

	def MigrateV2Content(self,parent,childType,log):
		"""flow typically maps to a div element.
		
		A flow with a specified class always becomes a div."""
		if self.flowClass is not None:
			if childType in (html.BlockMixin,html.FlowMixin):
				div=parent.ChildElement(html.Div,(qtiv2.IMSQTI_NAMESPACE,'div'))
				div.styleClass=self.flowClass
				QTIFlowMatContainer.MigrateV2Content(self,div,html.FlowMixin,log)
			else:
				span=parent.ChildElement(html.Span,(qtiv2.IMSQTI_NAMESPACE,'span'))
				span.styleClass=self.flowClass
				QTIFlowMatContainer.MigrateV2Content(self,span,html.InlineMixin,log)
		else:
			# ignore the flow, br handling is done automatically by the parent
			QTIFlowMatContainer.MigrateV2Content(self,parent,childType,log)


class QTIPresentationMaterial(QTICommentElement):
	"""Represent presentation_material element
	
::

	<!ELEMENT presentation_material (qticomment? , flow_mat+)>"""
	XMLNAME="presentation_material"
	XMLCONTENT=xml.XMLElementContent
	

class QTIReference(QTICommentElement):
	"""Represent presentation_material element
	
::

	<!ELEMENT reference (qticomment? , (material | mattext | matemtext | matimage | mataudio |
		matvideo | matapplet | matapplication | matbreak | mat_extension)+)>"""
	XMLNAME="reference"
	XMLCONTENT=xml.XMLElementContent
	

class QTISelectionOrdering(QTICommentElement):
	"""Represent selection_ordering element.
	
::

	<!ELEMENT selection_ordering (qticomment? , sequence_parameter* , selection* , order?)>
	
	<!ATTLIST selection_ordering  sequence_type CDATA  #IMPLIED >"""
	XMLNAME="selection_ordering"
	XMLCONTENT=xml.XMLElementContent
		

class QTIOutcomesProcessing(QTICommentElement):
	"""Represent outcomes_processing element.
	
::

	<!ELEMENT outcomes_processing (qticomment? , outcomes , objects_condition* ,
		processing_parameter* , map_output* , outcomes_feedback_test*)>
	
	<!ATTLIST outcomes_processing  %I_ScoreModel; >"""
	XMLNAME="outcomes_processing"
	XMLCONTENT=xml.XMLElementContent

		
#
#	EXTENSION DEFINITIONS
#
class QTIMatExtension(QTIElement):
	"""Represents the mat_extension element.
	
::

	<!ELEMENT mat_extension ANY>
	"""
	XMLNAME="mat_extension"
	XMLCONTENT=xml.XMLMixedContent


class QTIVarExtension(QTIElement):
	"""Represents the var_extension element.
	
::

	<!ELEMENT var_extension ANY>
	"""
	XMLNAME="var_extension"
	XMLCONTENT=xml.XMLMixedContent


class QTIResponseExtension(QTIElement):
	"""Represents the response_extension element.
	
::

	<!ELEMENT response_extension ANY>
	"""
	XMLNAME="response_extension"
	XMLCONTENT=xml.XMLMixedContent


class QTIRenderExtension(QTIElement):
	"""Represents the render_extension element.
	
::

	<!ELEMENT render_extension ANY>
	"""
	XMLNAME="render_extension"
	XMLCONTENT=xml.XMLMixedContent


class QTIAssessProcExtension(QTIElement):
	"""Represents the render_extension element.
	
::

	<!ELEMENT assessproc_extension ANY>
	"""
	XMLNAME="assessproc_extension"
	XMLCONTENT=xml.XMLMixedContent


class QTISectionProcExtension(QTIElement):
	"""Represents the sectionproc_extension element.
	
::

	<!ELEMENT sectionproc_extension ANY>
	"""
	XMLNAME="sectionproc_extension"
	XMLCONTENT=xml.XMLMixedContent


class QTIItemProcExtension(QTIContentMixin,QTIElement):
	"""Represents the itemproc_extension element.
	
::

	<!ELEMENT itemproc_extension ANY>
	"""
	XMLNAME="itemproc_extension"
	XMLCONTENT=xml.XMLMixedContent

	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		QTIContentMixin.__init__(self)
		
	def MigrateV2Rule(self,cMode,ruleContainer,log):
		"""Converts an itemProcExtension into v2 response processing rules.
		
		We only support one type of extension at the moment, the
		humanrater element used as an illustration in the specification
		examples.
		"""
		for child in self.GetChildren():
			if type(child) in StringTypes:
				# ignore data
				continue
			elif child.xmlname=='humanraterdata':
				# humanraterdata extension, migrate content with appropriate view
				v2Item=ruleContainer.FindParent(qtiv2.QTIAssessmentItem)
				rubric=v2Item.ChildElement(qtiv2.QTIItemBody).ChildElement(qtiv2.QTIRubricBlock)
				rubric.view=qtiv2.QTIView.scorer
				material=[]
				child.FindChildren(QTIMaterial,material)
				self.MigrateV2Content(rubric,html.BlockMixin,log,material)
		return cMode,ruleContainer


class QTIRespCondExtension(QTIElement):
	"""Represents the respcond_extension element.
	
::

	<!ELEMENT respcond_extension ANY>
	"""
	XMLNAME="respcond_extension"
	XMLCONTENT=xml.XMLMixedContent


class QTISelectionExtension(QTIElement):
	"""Represents the selection_extension element.
	
::

	<!ELEMENT selection_extension ANY>
	"""
	XMLNAME="selection_extension"
	XMLCONTENT=xml.XMLMixedContent


class QTIObjectsCondExtension(QTIElement):
	"""Represents the objectscond_extension element.
	
::

	<!ELEMENT objectscond_extension (#PCDATA)>
	"""
	XMLNAME="objectscond_extension"
	XMLCONTENT=xml.XMLMixedContent


class QTIOrderExtension(QTIElement):
	"""Represents the order_extension element.
	
::

	<!ELEMENT order_extension ANY>
	"""
	XMLNAME="order_extension"
	XMLCONTENT=xml.XMLMixedContent


#
#	OBJECT-BANK OBJECT DEFINITIONS
#
class QTIObjectBank(QTICommentElement):
	"""Represents the objectbank element.
	
::

	<!ELEMENT objectbank (qticomment? , qtimetadata* , (section | item)+)>
	
	<!ATTLIST objectbank  %I_Ident; >
	"""
	XMLNAME="objectbank"
	XMLCONTENT=xml.XMLElementContent


#
#	ASSESSMENT OBJECT DEFINITIONS
#
class QTIAssessment(QTICommentElement):
	"""Represents the assessment element.
	
::

	<!ELEMENT assessment (qticomment? ,
		duration? ,
		qtimetadata* ,
		objectives* ,
		assessmentcontrol* ,
		rubric* ,
		presentation_material? ,
		outcomes_processing* ,
		assessproc_extension? ,
		assessfeedback* ,
		selection_ordering? ,
		reference? ,
		(sectionref | section)+
		)>
	
	<!ATTLIST assessment  %I_Ident;
						   %I_Title;
						   xml:lang CDATA  #IMPLIED >
	"""
	XMLNAME="assessment"
	XMLATTR_ident='ident'		
	XMLATTR_title='title'
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTICommentElement.__init__(self,parent)
		self.ident=None
		self.title=None
		self.QTIDuration=None
		self.QTIMetadata=[]
		self.QTIObjectives=[]
		self.QTIAssessmentControl=[]
		self.QTIRubric=[]
		self.QTIPresentationMaterial=None
		self.QTIOutcomesProcessing=[]
		self.QTIAssessProcExtension=None
		self.QTIAssessFeedback=[]
		self.QTISelectionOrdering=None
		self.QTIReference=None
		self.objectList=[]
		
	def QTISectionRef(self):
		child=QTISectionRef(self)
		self.objectList.append(child)
		return child
		
	def QTISection(self):
		child=QTISection(self)
		self.objectList.append(child)
		return child
		
	def GetChildren(self):
		children=QTIComment.GetChildren(self)
		children=children+self.QTIMetadata+self.QTIObjectives+self.QTIAssessmentControl+self.QTIRubric
		xml.OptionalAppend(children,self.QTIPresentationMaterial)
		children=children+QTIOutcomesProcessing
		xml.OptionalAppend(children,self.QTIAssessProcExtension)
		children=children+self.QTIAssessFeedback
		xml.OptionalAppend(children,self.QTISelectionOrdering)
		xml.OptionalAppend(children,self.QTIReference)
		return children+self.objectList

	def MigrateV2(self,output):
		"""Converts this assessment to QTI v2
		
		For details, see QTIQuesTestInterop.MigrateV2."""
		for object in self.objectList:
			object.MigrateV2(output)


class QTIAssessmentControl(QTICommentElement):
	"""Represents the assessmentcontrol element.
	
::

	<!ELEMENT assessmentcontrol (qticomment?)>

	<!ATTLIST assessmentcontrol  %I_HintSwitch;
                              %I_SolutionSwitch;
                              %I_View;
                              %I_FeedbackSwitch; >
    """
	XMLNAME='assessmentcontrol'
	XMLCONTENT=xml.XMLElementContent	


class QTIAssessmentFeedback(QTICommentElement):
	"""Represents the assessfeedback element.
	
::

	<!ELEMENT assessfeedback (qticomment? , (material+ | flow_mat+))>
	
	<!ATTLIST assessfeedback  %I_View;
							   %I_Ident;
							   %I_Title; >
    """
	XMLNAME='assessfeedback'
	XMLCONTENT=xml.XMLElementContent


class QTIAssessmentFeedback(QTIElement):
	"""Represents the sectionref element.
	
::

	<!ELEMENT sectionref (#PCDATA)>
	
	<!ATTLIST sectionref  %I_LinkRefId; >
    """
	XMLNAME='sectionref'
	XMLCONTENT=xml.XMLMixedContent


#
#	SECTION OBJECT DEFINITIONS
#
class QTISection(QTICommentElement):
	"""Represents section element.
::

	<!ELEMENT section (qticomment? ,
		duration? ,
		qtimetadata* ,
		objectives* ,
		sectioncontrol* ,
		sectionprecondition* ,
		sectionpostcondition* ,
		rubric* ,
		presentation_material? ,
		outcomes_processing* ,
		sectionproc_extension? ,
		sectionfeedback* ,
		selection_ordering? ,
		reference? ,
		(itemref | item | sectionref | section)*
		)>
	
	<!ATTLIST section  %I_Ident;
						%I_Title;
						xml:lang CDATA  #IMPLIED >
	"""
	XMLNAME="section"
	XMLATTR_ident='ident'		
	XMLATTR_title='title'	
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTICommentElement.__init__(self,parent)
		self.ident=None
		self.title=None
		self.QTIDuration=None
		self.QTIMetadata=[]
		self.QTIObjectives=[]
		self.QTISectionControl=[]
		self.QTISectionPrecondition=[]
		self.QTISectionPostcondition=[]
		self.QTIRubric=[]
		self.QTIPresentationMaterial=None
		self.QTIOutcomesProcessing=[]
		self.QTISectionProcExtension=None
		self.QTISectionFeedback=[]
		self.QTISelectionOrdering=None
		self.QTIReference=None
		self.objectList=[]
		
	def QTIItemRef(self):
		child=QTIItemRef(self)
		self.objectList.append(child)
		return child
		
	def QTIItem(self):
		child=QTIItem(self)
		self.objectList.append(child)
		return child
		
	def QTISectionRef(self):
		child=QTISectionRef(self)
		self.objectList.append(child)
		return child
		
	def QTISection(self):
		child=QTISection(self)
		self.objectList.append(child)
		return child
		
	def GetChildren(self):
		children=QTIComment.GetChildren(self)
		children=children+self.QTIMetadata+self.QTIObjectives+self.QTISectionControl+self.QTISectionPrecondition+self.QTISectionPostcondition+self.QTIRubric
		xml.OptionalAppend(children,self.QTIPresentationMaterial)
		children=children+QTIOutcomesProcessing
		xml.OptionalAppend(children,self.QTISectionProcExtension)
		children=children+self.QTISectionFeedback
		xml.OptionalAppend(children,self.QTISelectionOrdering)
		xml.OptionalAppend(children,self.QTIReference)
		return children+self.objectList

	def MigrateV2(self,output):
		"""Converts this section to QTI v2
		
		For details, see QTIQuesTestInterop.MigrateV2."""
		for object in self.objectList:
			object.MigrateV2(output)
	
	
class QTISectionPrecondition(QTIElement):
	"""Represents the sectionprecondition element.
	
::

	<!ELEMENT sectionprecondition (#PCDATA)>"""
	XMLNAME='sectionprecondition'
	XMLCONTENT=xml.XMLMixedContent


class QTISectionPostcondition(QTIElement):
	"""Represents the sectionpostcondition element.
	
::

	<!ELEMENT sectionpostcondition (#PCDATA)>"""
	XMLNAME='sectionpostcondition'
	XMLCONTENT=xml.XMLMixedContent


class QTISectionControl(QTICommentElement):
	"""Represents the sectioncontrol element.
	
::

	<!ELEMENT sectioncontrol (qticomment?)>
	
	<!ATTLIST sectioncontrol  %I_FeedbackSwitch;
							   %I_HintSwitch;
							   %I_SolutionSwitch;
							   %I_View; >
	"""
	XMLNAME='sectioncontrol'
	XMLCONTENT=xml.XMLMixedContent


class QTIItemRef(QTIElement):
	"""Represents the itemref element.
	
::

	<!ELEMENT itemref (#PCDATA)>
	
	<!ATTLIST itemref  %I_LinkRefId; >
	"""
	XMLNAME='itemref'
	XMLCONTENT=xml.XMLMixedContent


class QTISectionFeedback(QTICommentElement):
	"""Represents the sectionfeedback element.
	
::

	<!ELEMENT sectionfeedback (qticomment? , (material+ | flow_mat+))>
	
	<!ATTLIST sectionfeedback  %I_View;
								%I_Ident;
								%I_Title; >
	"""
	XMLNAME='sectionfeedback'
	XMLCONTENT=xml.XMLMixedContent


#
#	ITEM OBJECT DEFINITIONS
#
class QTIItem(QTICommentElement):
	"""Represents the item element.
	
::

	<!ELEMENT item (qticomment?
		duration?
		itemmetadata?
		objectives*
		itemcontrol*
		itemprecondition*
		itempostcondition*
		(itemrubric | rubric)*
		presentation?
		resprocessing*
		itemproc_extension?
		itemfeedback*
		reference?)>

	<!ATTLIST item  maxattempts CDATA  #IMPLIED
		%I_Label;
		%I_Ident;
		%I_Title;
		xml:lang    CDATA  #IMPLIED >"""
	XMLNAME='item'
	XMLATTR_ident='ident'
	XMLATTR_label='label'
	XMLATTR_maxattempts='maxattempts'		
	XMLATTR_title='title'
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTICommentElement.__init__(self,parent)
		self.maxattempts=None
		self.label=None
		self.ident=None
		self.title=None
		self.QTIDuration=None
		self.QTIItemMetadata=None
		self.QTIObjectives=[]
		self.QTIItemControl=[]
		self.QTIItemPrecondition=[]
		self.QTIItemPostcondition=[]
		self.QTIRubric=[]
		self.QTIPresentation=None
		self.QTIResProcessing=[]
		self.QTIItemProcExtension=None
		self.QTIItemFeedback=[]
		self.QTIReference=None
					
	def QTIItemRubric(self):
		"""itemrubric is deprecated in favour of rubric."""
		child=QTIItemRubric(self)
		self.QTIRubric.append(child)
		return child
		
	def GetChildren(self):
		children=QTIComment.GetChildren(self)
		xml.OptionalAppend(children,self.QTIDuration)
		xml.OptionalAppend(children,self.QTIItemMetadata)
		children=children+self.QITObjectives+self.QTIItemControl+self.QTIItemPrecondition+self.QTIPostCondition+self.QTIRubric
		xml.OptionalAppend(children,self.QTIPresentation)
		children=children+self.QTIResProcessing
		xml.OptionalAppend(children,self.QTIItemProcExtension)
		children=children+self.QTIItemFeedback
		xml.OptionalAppend(children,self.QTIReference)
		return children
	
	def MigrateV2(self,output):
		"""Converts this item to QTI v2
		
		For details, see QTIQuesTestInterop.MigrateV2."""
		# First thing we do is initialize any fixups
		for rp in self.QTIResProcessing:
			rp._interactionFixup={}
		doc=qtiv2.QTIDocument(root=qtiv2.QTIAssessmentItem)
		item=doc.root
		lom=imsmd.LOM(None)
		log=[]
		ident=qtiv2.MakeValidNCName(self.ident)
		if self.ident!=ident:
			log.append("Warning: illegal NCName for ident: %s, replaced with: %s"%(self.ident,ident))
		item.identifier=ident
		title=self.title
		# may be specified in the metadata
		if self.QTIItemMetadata:
			mdTitles=self.QTIItemMetadata.metadata.get('title',())
		else:
			mdTitles=()
		if title:
			item.title=title
		elif mdTitles:
			item.title=mdTitles[0][0]
		else:
			item.title=ident
		if self.maxattempts is not None:
			log.append("Warning: maxattempts can not be controlled at item level, ignored: maxattempts='"+self.maxattempts+"'")
		if self.label:
			item.label=self.label
		lang=self.GetLang()
		item.SetLang(lang)
		general=lom.LOMGeneral()
		id=general.LOMIdentifier()
		id.SetValue(self.ident)
		if title:
			lomTitle=general.ChildElement(imsmd.LOMTitle).LangString(title)
			if lang:
				lomTitle.SetLang(lang)
		if mdTitles:
			if title:
				# If we already have a title, then we have to add qmd_title as description metadata
				# you may think qmd_title is a better choice than the title attribute
				# but qmd_title is an extension so the title attribute takes precedence
				i=0
			else:
				lomTitle=general.ChildElement(imsmd.LOMTitle).LangString(mdTitles[0][0])
				lang=mdTitles[0][1].ResolveLang()
				if lang:
					lomTitle.SetLang(lang)
				i=1
			for mdTitle in mdTitles[i:]:
				lomTitle=general.LOMDescription().LangString(mdTitle[0])
				mdLang=mdTitle[1].ResolveLang()
				if mdLang:
					lomTitle.SetLang(mdLang)
		if self.QTIComment:
			# A comment on an item is added as a description to the metadata
			description=general.LOMDescription().LangString(self.QTIComment.GetValue())
		if self.QTIDuration:
			log.append("Warning: duration is currently outside the scope of version 2: ignored "+self.QTIDuration.GetValue())
		if self.QTIItemMetadata:
			self.QTIItemMetadata.MigrateV2(doc,lom,log)
		for objective in self.QTIObjectives:
			if objective.view.lower()!='all':
				objective.MigrateV2(item,log)
			else:
				objective.LRMMigrateObjectives(lom,log)
		if self.QTIItemControl:
			log.append("Warning: itemcontrol is currently outside the scope of version 2")
		for rubric in self.QTIRubric:
			rubric.MigrateV2(item,log)
		if self.QTIPresentation:
			self.QTIPresentation.MigrateV2(item,log)
		if self.QTIResProcessing:
			if len(self.QTIResProcessing)>1:
				log.append("Warning: multiople <resprocessing> not supported, ignoring all but the last")
			self.QTIResProcessing[-1].MigrateV2(item,log)
		for feedback in self.QTIItemFeedback:
			feedback.MigrateV2(item,log)
		output.append((doc, lom, log))
		#print doc.root
		

class QTIItemMetadata(QTIMetadataContainer):
	"""Represents the QTIItemMetadata element.
	
	This element contains more structure than is in common use, at the moment we
	represent this structure directly and automaticaly conform output to it,
	adding extension elements at the end.  In the future we might be more
	generous and allow input *and* output of elements in any sequence and
	provide separate methods for conforming these elements.
	
::

	<!ELEMENT itemmetadata (
		qtimetadata*
		qmd_computerscored?
		qmd_feedbackpermitted?
		qmd_hintspermitted?
		qmd_itemtype?
		qmd_levelofdifficulty?
		qmd_maximumscore?
		qmd_renderingtype*
		qmd_responsetype*
		qmd_scoringpermitted?
		qmd_solutionspermitted?
		qmd_status?
		qmd_timedependence?
		qmd_timelimit?
		qmd_toolvendor?
		qmd_topic?
		qmd_weighting?
		qmd_material*
		qmd_typeofsolution?
		)>
	"""
	XMLNAME='itemmetadata'
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIMetadataContainer.__init__(self,parent)
		self.QTIMetadata=[]
		self.QMDComputerScored=None
		self.QMDFeedbackPermitted=None
		self.QMDHintsPermitted=None
		self.QMDItemType=None
		self.QMDLevelOfDifficulty=None
		self.QMDMaximumScore=None
		self.QMDRenderingType=[]
		self.QMDResponseType=[]
		self.QMDScoringPermitted=None
		self.QMDSolutionsPermitted=None
		self.QMDStatus=None
		self.QMDTimeDependence=None
		self.QMDTimeLimit=None
		self.QMDToolVendor=None
		self.QMDTopic=None
		self.QMDWeighting=None
		self.QMDMaterial=[]
		self.QMDTypeOfSolution=None
		# Extensions in common use....
		self.QMDAuthor=[]
		self.QMDDescription=[]
		self.QMDDomain=[]
		self.QMDKeywords=[]
		self.QMDOrganization=[]
		self.QMDTitle=None
		
	def GetChildren(self):
		children=self.QTIMetadata[:]
		xml.OptionalAppend(children,self.QMDComputerScored)
		xml.OptionalAppend(children,self.QMDFeedbackPermitted)
		xml.OptionalAppend(children,self.QMDHintsPermitted)
		xml.OptionalAppend(children,self.QMDItemType)
		xml.OptionalAppend(children,self.QMDLevelOfDifficulty)
		xml.OptionalAppend(children,self.QMDMaximumScore)
		children=children+self.QMDRenderingType+self.QMDResponseType
		xml.OptionalAppend(children,self.QMDScoringPermitted)
		xml.OptionalAppend(children,self.QMDSolutionsPermitted)
		xml.OptionalAppend(children,self.QMDStatus)
		xml.OptionalAppend(children,self.QMDTimeDependence)
		xml.OptionalAppend(children,self.QMDTimeLimit)
		xml.OptionalAppend(children,self.QMDToolVendor)
		xml.OptionalAppend(children,self.QMDTopic)
		xml.OptionalAppend(children,self.QMDWeighting)
		children=children+self.QMDMaterial
		xml.OptionalAppend(children,self.QMDTypeOfSolution)
		children=children+self.QMDAuthor+self.QMDDescription+self.QMDDomain+self.QMDKeywords+self.QMDOrganization
		xml.OptionalAppend(children,self.QMDTitle)
		return children+QTIMetadataContainer.GetChildren(self)
	
	def LRMMigrateLevelOfDifficulty(self,lom,log):
		difficulty=self.metadata.get('levelofdifficulty',())
		for value,definition in difficulty:
			# IMS Definition says: The options are: "Pre-school", "School" or
			# "HE/FE", # "Vocational" and "Professional Development" so we bind
			# this value to the "Context" in LOM if one of the QTI or LOM
			# defined terms have been used, otherwise, we bind to Difficulty, as
			# this seems to be more common usage.
			context,lomFlag=QMDLevelOfDifficulty.LOMContextMap.get(value.lower(),(None,False))
			educational=lom.ChildElement(imsmd.LOMEducational)
			if context is None:
				# add value as difficulty
				value,lomFlag=QMDLevelOfDifficulty.LOMDifficultyMap.get(value.lower(),(value,False))
				d=educational.ChildElement(imsmd.LOMDifficulty)
				if lomFlag:
					d.LRMSource.LangString.SetValue(imsmd.LOM_SOURCE)
				else:
					d.LRMSource.LangString.SetValue(imsmd.LOM_UNKNOWNSOURCE)					
				d.LRMSource.LangString.SetLang("x-none")
				d.LRMValue.LangString.SetValue(value)
				d.LRMValue.LangString.SetLang("x-none")
			else:
				# add value as educational context
				c=educational.ChildElement(imsmd.LOMContext)
				if lomFlag:
					c.LRMSource.LangString.SetValue(imsmd.LOM_SOURCE)
				else:
					c.LRMSource.LangString.SetValue(imsmd.LOM_UNKNOWNSOURCE)					
				c.LRMSource.LangString.SetLang("x-none")
				c.LRMValue.LangString.SetValue(context)
				c.LRMValue.LangString.SetLang("x-none")
	
	def LRMMigrateStatus(self,lom,log):
		status=self.metadata.get('status',())
		for value,definition in status:
			s=lom.ChildElement(imsmd.LOMLifecycle).ChildElement(imsmd.LOMStatus)
			value=value.lower()
			source=QMDStatusSourceMap.get(value,imsmd.LOM_UNKNOWNSOURCE)
			s.LRMSource.LangString.SetValue(source)
			s.LRMSource.LangString.SetLang("x-none")
			s.LRMValue.LangString.SetValue(value)
			s.LRMValue.LangString.SetLang("x-none")
	
	def LRMMigrateTopic(self,lom,log):
		topics=self.metadata.get('topic',())
		for value,definition in topics:
			lang=definition.ResolveLang()
			value=value.strip()
			description=lom.ChildElement(imsmd.LOMEducational).ChildElement(imsmd.LOMDescription)
			description.AddString(lang,value)
	
	def LRMMigrateContributor(self,fieldName,lomRole,lom,log):
		contributors=self.metadata.get(fieldName,())
		if contributors:
			if imsmd.vobject is None:
				log.append('Warning: qmd_%s support disabled (vobject not installed)'%fieldName)
			else:
				for value,definition in contributors:
					lifecycle=lom.ChildElement(imsmd.LOMLifecycle)
					contributor=lifecycle.ChildElement(imsmd.LOMContribute)
					role=contributor.LOMRole
					role.LRMSource.LangString.SetValue(imsmd.LOM_SOURCE)
					role.LRMSource.LangString.SetLang("x-none")
					role.LRMValue.LangString.SetValue(lomRole)
					role.LRMValue.LangString.SetLang("x-none")
					names=value.strip().split(',')
					for name in names:
						if not name.strip():
							continue
						vcard=imsmd.vobject.vCard()
						vcard.add('n')
						vcard.n.value=imsmd.vobject.vcard.Name(family=name,given='')
						vcard.add('fn')
						vcard.fn.value=name.strip()
						contributor.ChildElement(imsmd.LOMCEntity).LOMVCard.SetValue(vcard)	
	
	def LRMMigrateDescription(self,lom,log):
		descriptions=self.metadata.get('description',())
		for value,definition in descriptions:
			lang=definition.ResolveLang()
			genDescription=lom.ChildElement(imsmd.LOMGeneral).ChildElement(imsmd.LOMDescription).LangString(value)
			if lang:
				genDescription.SetLang(lang)

	def LRMMigrateDomain(self,lom,log):
		domains=self.metadata.get('domain',())
		warn=False
		for value,definition in domains:
			lang=definition.ResolveLang()
			kwValue=value.strip()
			if kwValue:
				kwContainer=lom.ChildElement(imsmd.LOMGeneral).ChildElement(imsmd.LOMKeyword).LangString(kwValue)
				# set the language of the kw
				if lang:
					kwContainer.SetLang(lang)
				if not warn:
					log.append("Warning: qmd_domain extension field will be added as LOM keyword")
					warn=True
	
	def LRMMigrateKeywords(self,lom,log):
		keywords=self.metadata.get('keywords',())
		for value,definition in keywords:
			lang=definition.ResolveLang()
			values=string.split(value,',')
			for kwValue in values:
				v=kwValue.strip()
				if v:
					kwContainer=lom.ChildElement(imsmd.LOMGeneral).ChildElement(imsmd.LOMKeyword).LangString(v)
					# set the language of the kw
					if lang:
						kwContainer.SetLang(lang)
	
	def LRMMigrateOrganization(self,lom,log):
		organizations=self.metadata.get('organization',())
		if organizations:
			if imsmd.vobject is None:
				log.append('Warning: qmd_organization support disabled (vobject not installed)')
			else:
				for value,definition in organizations:
					lifecycle=lom.ChildElement(imsmd.LOMLifecycle)
					contributor=lifecycle.ChildElement(imsmd.LOMContribute)
					role=contributor.LOMRole
					role.LRMSource.LangString.SetValue(imsmd.LOM_SOURCE)
					role.LRMSource.LangString.SetLang("x-none")
					role.LRMValue.LangString.SetValue("unknown")
					role.LRMValue.LangString.SetLang("x-none")
					name=value.strip()
					vcard=imsmd.vobject.vCard()
					vcard.add('n')
					vcard.n.value=imsmd.vobject.vcard.Name(family=name,given='')
					vcard.add('fn')
					vcard.fn.value=name
					vcard.add('org')
					vcard.org.value=[name]
					contributor.ChildElement(imsmd.LOMCEntity).LOMVCard.SetValue(vcard)	
			
	def MigrateV2(self,doc,lom,log):
		item=doc.root
		itemtypes=self.metadata.get('itemtype',())
		for itemtype,itemtypeDef in itemtypes:
			log.append("Warning: qmd_itemtype now replaced by qtiMetadata.interactionType in manifest, ignoring %s"%itemtype)
		self.LRMMigrateLevelOfDifficulty(lom,log)
		self.LRMMigrateStatus(lom,log)
		vendors=self.metadata.get('toolvendor',())
		for value,definition in vendors:
			item.metadata.ChildElement(qtiv2.QMDToolVendor).SetValue(value)
		self.LRMMigrateTopic(lom,log)
		self.LRMMigrateContributor('author','author',lom,log)
		self.LRMMigrateContributor('creator','initiator',lom,log)
		self.LRMMigrateContributor('owner','publisher',lom,log)
		self.LRMMigrateDescription(lom,log)
		self.LRMMigrateDomain(lom,log)
		self.LRMMigrateKeywords(lom,log)
		self.LRMMigrateOrganization(lom,log)

	
class QTIItemControl(QTICommentElement,QTIViewMixin):
	"""Represents the itemcontrol element
	
::

	<!ELEMENT itemcontrol (qticomment?)>
	
	<!ATTLIST itemcontrol  %I_FeedbackSwitch;
							%I_HintSwitch;
							%I_SolutionSwitch;
							%I_View; >
	"""
	XMLNAME='itemcontrol'
	XMLATTR_feedbackswitch=('feedbackSwitch',ParseYesNo,FormatYesNo)
	XMLATTR_hintswitch=('hintSwitch',ParseYesNo,FormatYesNo)
	XMLATTR_solutionswitch=('solutionSwitch',ParseYesNo,FormatYesNo)
	XMLCONTENT=xml.XMLElementContent

	def __init__(self,parent):
		QTICommentElement.__init__(self,parent)
		QTIViewMixin.__init__(self)
		self.feedbackSwitch=True
		self.hintSwitch=True
		self.solutionSwitch=True	

	def GetChildren(self):
		children=QTICommentElement.GetChildren(self)
		return children
				

class QTIItemPreCondition(QTIElement):
	"""Represents the itemprecondition element
	
::

	<!ELEMENT itemprecondition (#PCDATA)>"""
	XMLNAME='itemprecondition'
	XMLCONTENT=xml.XMLMixedContent


class QTIItemPostCondition(QTIElement):
	"""Represents the itempostcondition element
	
::

	<!ELEMENT itempostcondition (#PCDATA)>"""
	XMLNAME='itempostcondition'
	XMLCONTENT=xml.XMLMixedContent


class QTIItemRubric(QTIRubric):
	"""Represents the itemrubric element.
	
::

	<!ELEMENT itemrubric (material)>

	<!ATTLIST itemrubric  %I_View; >
	
	We are generous with this element, extending the allowable content model
	to make it equivalent to <rubric> which is a superset.  <itemrubric> was
	deprecated in favour of <rubric> with QTI v1.2
	"""
	XMLNAME='itemrubric'
	XMLCONTENT=xml.XMLElementContent


class QTIPresentation(QTIFlowContainer,QTIPositionMixin):
	"""Represents the presentation element.
	
::

	<!ELEMENT presentation (qticomment? ,
		(flow |
			(material |
			response_lid |
			response_xy |
			response_str |
			response_num |
			response_grp |
			response_extension)+
			)
		)>
	
	<!ATTLIST presentation  %I_Label;
							 xml:lang CDATA  #IMPLIED
							 %I_Y0;
							 %I_X0;
							 %I_Width;
							 %I_Height; >"""
	XMLNAME='presentation'
	XMLATTR_label='label'	
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIFlowContainer.__init__(self,parent)
		QTIPositionMixin.__init__(self)
		self.label=None
		
	def MigrateV2(self,v2Item,log):
		"""Presentation maps to the main content in itemBody."""
		itemBody=v2Item.ChildElement(qtiv2.QTIItemBody)
		if self.GotPosition():
			log.append("Warning: discarding absolute positioning information on presentation")
		if self.InlineChildren():
			p=itemBody.ChildElement(html.P,(qtiv2.IMSQTI_NAMESPACE,'p'))
			if self.label is not None:
				#p.label=self.label
				p.SetAttribute('label',self.label)
			self.MigrateV2Content(p,html.InlineMixin,log)
		elif self.label is not None:
			# We must generate a div to hold the label, we can't rely on owning the whole itemBody
			div=itemBody.ChildElement(html.Div,(qtiv2.IMSQTI_NAMESPACE,'div'))
			div.SetAttribute('label',self.label)
			# Although div will take an inline directly we force blocking at the top level
			self.MigrateV2Content(div,html.BlockMixin,log)
		else:
			# mixture or block children, force use of blocks
			self.MigrateV2Content(itemBody,html.BlockMixin,log)
		self.CleanHotspotImages(itemBody)
	
	def CleanHotspotImages(self,itemBody):
		"""Removes spurious img tags which represent images used in hotspotInteractions.
		
		Unfortunately we have to do this because images needed in hotspot interactions
		are often clumsily placed outside the response/render constructs.  Rather than
		fiddle around at the time we simply migrate the lot, duplicating the images
		in the hotspotInteractions.  When the itemBody is complete we do a grand tidy
		up to remove spurious images."""
		hotspots=[]
		itemBody.FindChildren((qtiv2.QTIHotspotInteraction,qtiv2.QTISelectPointInteraction),hotspots)
		images=[]
		itemBody.FindChildren(html.Img,images)
		for hs in hotspots:
			for img in images:
				# migrated images/hotspots will always have absolute URIs
				if img.src and str(img.src)==str(hs.Object.data):
					parent=img.parent
					parent.DeleteChild(img)
					if isinstance(parent,html.P) and len(parent.GetChildren())==0:
						# It is always safe to remove a paragraph left empty by deleting an image
						# The chance are the paragraphic was created by us to house a matimage
						parent.parent.DeleteChild(parent)
					
		
	def IsInline(self):
		return False
		

class QTIFlow(QTIFlowContainer):
	"""Represents the flow element.
	
::

	<!ELEMENT flow (qticomment? ,
		(flow |
		material |
		material_ref |
		response_lid |
		response_xy |
		response_str |
		response_num |
		response_grp |
		response_extension)+
		)>
	
	<!ATTLIST flow  %I_Class; >
	"""
	XMLNAME='flow'
	XMLATTR_class='flowClass'
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIFlowContainer.__init__(self,parent)
		self.flowClass=None
		
	def IsInline(self):
		"""flow is always treated as a block if flowClass is specified, otherwise
		it is treated as a block unless it is an only child."""
		if self.flowClass is None:
			return self.InlineChildren()
		else:
			return False

	def MigrateV2Content(self,parent,childType,log):
		"""flow typically maps to a div element.
		
		A flow with a specified class always becomes a div
		A flow with inline children generates a paragraph to hold them
		A flow with no class is ignored."""
		if self.flowClass is not None:
			if childType in (html.BlockMixin,html.FlowMixin):
				div=parent.ChildElement(html.Div,(qtiv2.IMSQTI_NAMESPACE,'div'))
				div.styleClass=self.flowClass
				QTIFlowContainer.MigrateV2Content(self,div,html.FlowMixin,log)
			else:
				span=parent.ChildElement(html.Span,(qtiv2.IMSQTI_NAMESPACE,'span'))
				span.styleClass=self.flowClass
				QTIFlowContainer.MigrateV2Content(self,span,html.InlineMixin,log)
		else:
			QTIFlowContainer.MigrateV2Content(self,parent,childType,log)
	

class QTIResponseThing(QTIElement,QTIContentMixin):
	"""Abstract class for the main response_* elements::
	
	<!ELEMENT response_* ((material | material_ref)? ,
		(render_choice | render_hotspot | render_slider | render_fib | render_extension) ,
		(material | material_ref)?)>

	<!ATTLIST response_*  %I_Rcardinality;
                         %I_Rtiming;
                         %I_Ident; >		
	"""
	XMLATTR_ident='ident'
	XMLATTR_rcardinality=('rCardinality',DecodeRCardinality,EncodeRCardinality)
	XMLATTR_rtiming=('rTiming',ParseYesNo,FormatYesNo)	
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		QTIContentMixin.__init__(self)
		self.ident=None
		self.rCardinality=QTIRCardinality.Single
		self.rTiming=False
		self.intro=[]
		self.prompt=[]
		self.inlinePrompt=True
		self.render=None
		self.outro=[]
		self.footer=[]
		self.inlineFooter=True

	def QTIMaterial(self):
		child=QTIMaterial(self)
		if self.render:
			self.outro.append(child)
		else:
			self.intro.append(child)
		return child
	
	def QTIMaterialRef(self):
		child=QTIMaterialRef(self)
		if self.render:
			self.outro.append(child)
		else:
			self.intro.append(child)
		return child
	
	def QTIRenderThing(self,childClass):
		child=childClass(self)
		self.render=child
		return child
		
	def QTIRenderExtension(self):
		child=QTIRenderExtension(self)
		self.render=child
		return child
	
	def GetChildren(self):
		children=self.intro[:]
		if self.render:
			children.append(self.render)
		return children+self.outro

	def ContentChanged(self):
		if isinstance(self.render,QTIRenderFIB) and self.render.MixedModel():
			# use simplified prompt logic.
			self.prompt=self.intro
			self.inlintPrompt=True
			for child in self.prompt:
				if not child.IsInline():
					self.inlinePrompt=False
			self.footer=self.outro			
			self.inlineFooter=True
			for child in self.footer:
				if not child.IsInline():
					self.inlineFooter=False
		elif self.render:
			# all the material up to the first response_label is the prompt
			self.prompt=[]
			self.inlinePrompt=True
			renderChildren=self.render.GetLabelContent()
			for child in self.intro+renderChildren:
				#print child.__class__,child.xmlname
				if isinstance(child,QTIResponseLabel):
					break
				self.prompt.append(child)
				if not child.IsInline():
					self.inlinePrompt=False
			self.footer=[]
			self.inlineFooter=True
			foundLabel=False
			for child in renderChildren+self.outro:
				if isinstance(child,QTIResponseLabel):
					self.footer=[]
					self.inlineFooter=True
					foundLabel=True
					continue
				if foundLabel:
					self.footer.append(child)
					if not child.IsInline():
						self.inlineFooter=False
			
	def InlineChildren(self):
		return self.inlinePrompt and (self.render is None or self.render.IsInline()) and self.inlineFooter

	def GetBaseType(self,interaction):
		"""Returns the base type to use for the given interaction."""
		raise QTIUnimplementedError("BaseType selection for %s"%self.__class__.__name__)

	def MigrateV2Content(self,parent,childType,log):
		if self.inlinePrompt:
			interactionPrompt=self.prompt
		else:
			if childType is html.InlineMixin:
				raise QTIError("Unexpected attempt to inline interaction")
			interactionPrompt=None
			if isinstance(self.render,QTIRenderHotspot):
				div=parent.ChildElement(html.Div,(qtiv2.IMSQTI_NAMESPACE,'div'))
				QTIContentMixin.MigrateV2Content(self,div,html.FlowMixin,log,self.prompt)
				# Now we need to find any images and pass them to render hotspot instead
				# which we do by reusing the interactionPrompt (currently we only find
				# the first image).
				interactionPrompt=[]
				div.FindChildren(html.Img,interactionPrompt,1)
			else:
				QTIContentMixin.MigrateV2Content(self,parent,childType,log,self.prompt)
		if self.render:
			interactionList=self.render.MigrateV2Interaction(parent,childType,interactionPrompt,log)
			item=parent.FindParent(qtiv2.QTIAssessmentItem)
			if len(interactionList)>1 and self.rCardinality==QTIRCardinality.Single:
				log.append("Error: unable to migrate a response with Single cardinality to a single interaction: %s"%self.ident) 
				interactionList=[]
				responseList=[]
			else:
				baseIdentifier=qtiv2.ValidateIdentifier(self.ident)
				responseList=[]
				if len(interactionList)>1:
					i=0
					for interaction in interactionList:
						i=i+1
						while True:
							rIdentifier="%s_%02i"%(baseIdentifier,i)
							if item is None or not item.IsDeclared(rIdentifier):
								break
						interaction.responseIdentifier=rIdentifier
						responseList.append(rIdentifier)
				elif interactionList:	
					interaction=interactionList[0]
					interaction.responseIdentifier=baseIdentifier
					responseList=[interaction.responseIdentifier]
			if item:
				for i,r in zip(interactionList,responseList):
					d=item.ChildElement(qtiv2.QTIResponseDeclaration)
					d.identifier=r
					d.cardinality=QTIRCardinality.MigrateV2[self.rCardinality]
					d.baseType=self.GetBaseType(interactionList[0])
					self.render.MigrateV2InteractionDefault(d,i)
					item.RegisterDeclaration(d)
				if len(responseList)>1:
					d=item.ChildElement(qtiv2.QTIOutcomeDeclaration)
					d.identifier=baseIdentifier
					d.cardinality=QTIRCardinality.MigrateV2[self.rCardinality]
					d.baseType=self.GetBaseType(interactionList[0])
					item.RegisterDeclaration(d)
					# now we need to fix this outcome up with a value in response processing
					selfItem=self.FindParent(QTIItem)
					if selfItem:
						for rp in selfItem.QTIResProcessing:
							rp._interactionFixup[baseIdentifier]=responseList
		# the footer is in no-man's land so we just back-fill
		QTIContentMixin.MigrateV2Content(self,parent,childType,log,self.footer)

	
class QTIResponseLId(QTIResponseThing):
	"""Represents the response_lid element::

	<!ELEMENT response_lid ((material | material_ref)? ,
		(render_choice | render_hotspot | render_slider | render_fib | render_extension) ,
		(material | material_ref)?)>

	<!ATTLIST response_lid  %I_Rcardinality;
                         %I_Rtiming;
                         %I_Ident; >
	"""
	XMLNAME='response_lid'
	
	def GetBaseType(self,interaction):
		"""We always return identifier for response_lid."""
		return qtiv2.BaseType.identifier

		
class QTIResponseXY(QTIResponseThing):
	"""Represents the response_xy element::

	<!ELEMENT response_xy ((material | material_ref)? ,
		(render_choice | render_hotspot | render_slider | render_fib | render_extension) ,
		(material | material_ref)?)>
	
	<!ATTLIST response_xy  %I_Rcardinality;
							%I_Rtiming;
							%I_Ident; >
	"""
	XMLNAME='response_xy'

	def GetBaseType(self,interaction):
		"""We always return identifier for response_lid."""
		if isinstance(interaction,qtiv2.QTISelectPointInteraction):
			return qtiv2.BaseType.point
		else:
			return QTIResponseThing.GetBaseType(self)


class QTIResponseStr(QTIResponseThing):
	"""Represents the response_str element.
	
::

	<!ELEMENT response_str ((material | material_ref)? ,
		(render_choice | render_hotspot | render_slider | render_fib | render_extension) ,
		(material | material_ref)?)>
	
	<!ATTLIST response_str  %I_Rcardinality;
							 %I_Ident;
							 %I_Rtiming; >
	"""
	XMLNAME='response_str'

	def GetBaseType(self,interaction):
		"""We always return string for response_str."""
		return qtiv2.BaseType.string


class QTIResponseNum(QTIResponseThing):
	"""Represents the response_num element.
	
::

	<!ELEMENT response_num ((material | material_ref)? ,
		(render_choice | render_hotspot | render_slider | render_fib | render_extension) ,
		(material | material_ref)?)>
	
	<!ATTLIST response_num  numtype         (Integer | Decimal | Scientific )  'Integer'
							 %I_Rcardinality;
							 %I_Ident;
							 %I_Rtiming; >
	"""
	XMLNAME='response_num'
	XMLATTR_numtype=('numType',DecodeNumType,EncodeNumType)	
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIResponseThing.__init__(self,parent)
		self.numType=NumType.Integer

	def GetBaseType(self,interaction):
		"""We always return string for response_str."""
		if self.numType==NumType.Integer:
			return qtiv2.BaseType.integer
		else:
			return qtiv2.BaseType.float


class QTIResponseGrp(QTIElement,QTIContentMixin):
	"""Represents the response_grp element.
	
::

	<!ELEMENT response_grp ((material | material_ref)? ,
		(render_choice | render_hotspot | render_slider | render_fib | render_extension) ,
		(material | material_ref)?)>
	
	<!ATTLIST response_grp  %I_Rcardinality;
							 %I_Ident;
							 %I_Rtiming; >
	"""
	XMLNAME='response_grp'
	XMLCONTENT=xml.XMLElementContent


class QTIResponseLabel(QTIElement,QTIContentMixin):
	"""Represents the response_label element.
	
::

	<!ELEMENT response_label (#PCDATA | qticomment | material | material_ref | flow_mat)*>
	
	<!ATTLIST response_label  rshuffle     (Yes | No )  'Yes'
							   rarea        (Ellipse | Rectangle | Bounded )  'Ellipse'
							   rrange       (Exact | Range )  'Exact'
							   labelrefid  CDATA  #IMPLIED
							   %I_Ident;
							   match_group CDATA  #IMPLIED
							   match_max   CDATA  #IMPLIED >
	"""
	XMLNAME='response_label'
	XMLATTR_ident='ident'
	XMLATTR_rshuffle=('rShuffle',ParseYesNo,FormatYesNo)
	XMLATTR_rarea=('rArea',DecodeArea,EncodeArea)
	XMLCONTENT=xml.XMLMixedContent

	def __init__(self,parent):
		"""Although we inherit from the QTIContentMixin class we don't define
		custom setters to capture child elements in the contentChildren list
		because this element has mixed content - though in practice it really
		should have either data or element content."""
		QTIElement.__init__(self,parent)
		QTIContentMixin.__init__(self)
		self.ident=''
		self.rShuffle=True
		self.rArea=None
	
	def IsInline(self):
		"""Whether or not a response_label is inline depends on the context...
		
		render_choice: a choice is a block
		render_hotspot: at most a label on the image so treated as inline
		render_fib: always inline
		"""
		render=self.FindParent(QTIRenderThing)
		if isinstance(render,QTIRenderChoice):
			return False
		elif isinstance(render,QTIRenderHotspot):
			return True
		elif isinstance(render,QTIRenderFIB):
			return render.InlineFIBLabel()
		else:
			return self.InlineChildren()
		
	def InlineChildren(self):
		children=QTIElement.GetChildren(self)
		for child in children:
			if type(child) in StringTypes:
				continue
			elif issubclass(child.__class__,QTIContentMixin):
				if child.IsInline():
					continue
				return False
			else:
				# QTIComment most likely
				continue
		return True
		
	def MigrateV2Content(self,parent,childType,log):
		"""Migrates this content to v2 adding it to the parent content node."""
		render=self.FindParent(QTIRenderThing)
		if isinstance(render,QTIRenderFIB):
			render.MigrateV2FIBLabel(self,parent,childType,log)
		
	def MigrateV2SimpleChoice(self,interaction,log):
		"""Migrate this label into a v2 simpleChoice in interaction."""
		choice=interaction.ChildElement(qtiv2.QTISimpleChoice)
		choice.identifier=qtiv2.ValidateIdentifier(self.ident)
		if isinstance(interaction,qtiv2.QTIChoiceInteraction) and interaction.shuffle:			
			choice.fixed=not self.rShuffle
		data=[]
		gotElements=False
		children=QTIElement.GetChildren(self)
		for child in children:
			if type(child) in StringTypes:
				if len(child.strip()):
					data.append(child)
			elif isinstance(child,QTIComment):
				continue
			else:
				gotElements=True
		if data and gotElements:
			log.append('Warning: ignoring PCDATA in <response_label>, "%s"'%string.join(data,' '))
		elif data:
			for d in data:
				choice.AddData(d)
		else:
			content=[]
			for child in children:
				if isinstance(child,QTIContentMixin):
					content.append(child)
			QTIContentMixin.MigrateV2Content(self,choice,html.FlowMixin,log,content)

	def MigrateV2HotspotChoice(self,interaction,log,xOffset=0,yOffset=0):
		"""Migrate this label into a v2 hotspotChoice in interaction."""
		if isinstance(interaction,qtiv2.QTISelectPointInteraction):
			log.append("Warning: ignoring response_label in selectPointInteraction (%s)"%self.ident)
			return
		choice=interaction.ChildElement(qtiv2.QTIHotspotChoice)
		choice.identifier=qtiv2.ValidateIdentifier(self.ident)
		# Hard to believe I know, but we sift the content of the response_label
		# into string data (which is parsed for coordinates) and elements which
		# have their text extracted for the hotspot label.
		lang,labelData,valueData=self.ParseValue()
		choice.shape,coords=MigrateV2AreaCoords(self.rArea,valueData,log)
		if xOffset or yOffset:
			qtiv2.OffsetShape(choice.shape,coords,xOffset,yOffset)
		for c in coords:
			choice.coords.values.append(html.LengthType(c))
		if lang is not None:
			choice.SetLang(lang)
		if labelData:
			choice.hotspotLabel=labelData
		
	def HotspotInImage(self,matImage):
		"""Tests this hotspot to see if it overlaps with matImage.
		
		The coordinates in the response label are interpreted relative to
		a notional 'stage' on which the presentation takes place.  If the
		image does not have X0,Y0 coordinates then it is ignored and
		we return 0.
		"""
		if matImage.x0 is None or matImage.y0 is None:
			return False
		if matImage.width is None or matImage.height is None:
			return False
		lang,label,value=self.ParseValue()
		shape,coords=MigrateV2AreaCoords(self.rArea,value,[])
		bounds=qtiv2.CalculateShapeBounds(shape,coords)
		if bounds[0]>matImage.x0+matImage.width or bounds[2]<matImage.x0:
			return False
		if bounds[1]>matImage.y0+matImage.height or bounds[3]<matImage.y0:
			return False
		return True
	
	def ParseValue(self):
		"""Returns lang,label,coords parsed from the value."""
		valueData=[]
		labelData=[]
		lang=None
		for child in self.GetChildren():
			if type(child) in StringTypes:
				valueData.append(child)
			else:
				childLang,text=child.ExtractText()
				if lang is None and childLang is not None:
					lang=childLang
				labelData.append(text)
		valueData=string.join(valueData,' ')
		labelData=string.join(labelData,' ')
		return lang,labelData,valueData
	
	
class QTIFlowLabel(QTICommentElement,QTIContentMixin):
	"""Represents the flow_label element.
	
::

	<!ELEMENT flow_label (qticomment? , (flow_label | response_label)+)>
	
	<!ATTLIST flow_label  %I_Class; >
	"""
	XMLNAME='flow_label'
	XMLCONTENT=xml.XMLElementContent

	def __init__(self,parent):
		QTICommentElement.__init__(self,parent)
		QTIContentMixin.__init__(self)
	
	def QTIFlowLabel(self):
		child=QTIFlowLabel(self)
		self.contentChildren.append(child)
		return child
	
	def QTIResponseLabel(self):
		child=QTIResponseLabel(self)
		self.contentChildren.append(child)
		return child

	def GetChildren(self):
		children=QTICommentElement.GetChildren(self)+self.contentChildren
		return children
		
	def GetLabelContent(self):
		children=[]
		for child in self.contentChildren:
			if isinstance(child,QTIFlowLabel):
				children=children+child.GetLabelContent()
			else:
				children.append(child)
		return children


class QTIResponseNA(QTIElement):
	"""Represents the response_na element.
	
::

	<!ELEMENT response_na ANY>"""
	XMLNAME='response_na'
	XMLCONTENT=xml.XMLMixedContent
	

class QTIRenderThing(QTIElement,QTIContentMixin):
	"""Abstract base class for all render_* objects::
	
	<!ELEMENT render_* ((material | material_ref | response_label | flow_label)* , response_na?)>	
	"""
	XMLCONTENT=xml.XMLElementContent

	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		QTIContentMixin.__init__(self)
		self.QTIResponseNA=None

	def QTIMaterial(self):
		child=QTIMaterial(self)
		self.contentChildren.append(child)
		return child
		
	def QTIMaterialRef(self):
		child=QTIMaterialRef(self)
		self.contentChildren.append(child)
		return child
		
	def QTIResponseLabel(self):
		child=QTIResponseLabel(self)
		self.contentChildren.append(child)
		return child
		
	def QTIFlowLabel(self):
		child=QTIFlowLabel(self)
		self.contentChildren.append(child)
		return child
		
	def GetChildren(self):
		children=self.contentChildren[:]
		xml.OptionalAppend(children,self.QTIResponseNA)
		return children
	
	def GetLabelContent(self):
		children=[]
		for child in self.contentChildren:
			if isinstance(child,QTIFlowLabel):
				children=children+child.GetLabelContent()
			else:
				children.append(child)
		return children

	def IsInline(self):
		for child in self.GetLabelContent():
			if not child.IsInline():
				return False
		return True

	def MigrateV2Interaction(self,parent,childType,prompt,log):
		raise QTIUnimplementedError("%s x %s"%(self.parent.__class__.__name__,self.__class__.__name__))
		
	def MigrateV2InteractionDefault(self,parent,interaction):
		# Most interactions do not need default values.
		pass

		
class QTIRenderChoice(QTIRenderThing):
	"""Represents the render_choice element.
	
::

	<!ELEMENT render_choice ((material | material_ref | response_label | flow_label)* , response_na?)>
	
	<!ATTLIST render_choice  shuffle      (Yes | No )  'No'
							  %I_MinNumber;
							  %I_MaxNumber; >
	"""
	XMLNAME='render_choice'
	XMLATTR_maxnumber=('maxNumber',ParseInteger,FormatInteger)
	XMLATTR_minnumber=('minNumber',ParseInteger,FormatInteger)
	XMLATTR_shuffle=('shuffle',ParseYesNo,FormatYesNo)
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIRenderThing.__init__(self,parent)
		self.shuffle=False
		self.minNumber=None
		self.maxNumber=None
	
	def IsInline(self):
		"""This always results in a block-like interaction."""
		return False
		
	def MigrateV2Interaction(self,parent,childType,prompt,log):
		"""Migrates this content to v2 adding it to the parent content node."""
		interaction=None
		if isinstance(self.parent,QTIResponseLId):
			if childType is html.InlineMixin:
				raise QTIError("Unexpected attempt to put block interaction in inline context")
			if self.parent.rCardinality==QTIRCardinality.Ordered:
				raise QTIUnimplementedError("OrderInteraction")
			else:
				interaction=parent.ChildElement(qtiv2.QTIChoiceInteraction)
		else:		
			raise QTIUnimplementedError("%s x render_choice"%self.parent.__class__.__name__)
		if prompt:
			interactionPrompt=interaction.ChildElement(qtiv2.QTIPrompt)
			for child in prompt:
				child.MigrateV2Content(interactionPrompt,html.InlineMixin,log)			
		if self.minNumber is not None:
			interaction.minChoices=self.minNumber
		if self.maxNumber is not None:
			interaction.maxChoices=self.maxNumber
		interaction.shuffle=self.shuffle
		for child in self.GetLabelContent():
			if isinstance(child,QTIResponseLabel):
				child.MigrateV2SimpleChoice(interaction,log)
		return [interaction]

		
class QTIRenderHotspot(QTIRenderThing):
	"""Represents the render_hotspot element.
	
::

	<!ELEMENT render_hotspot ((material | material_ref | response_label | flow_label)* , response_na?)>
	
	<!ATTLIST render_hotspot  %I_MaxNumber;
							   %I_MinNumber;
							   showdraw     (Yes | No )  'No' >
	"""
	XMLNAME='render_hotspot'
	XMLATTR_maxnumber=('maxNumber',ParseInteger,FormatInteger)
	XMLATTR_minnumber=('minNumber',ParseInteger,FormatInteger)
	XMLATTR_showdraw=('showDraw',ParseYesNo,FormatYesNo)
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIRenderThing.__init__(self,parent)
		self.minNumber=None
		self.maxNumber=None
		self.showDraw=False
	
	def IsInline(self):
		"""This always results in a block-like interaction."""
		return False

	def MigrateV2Interaction(self,parent,childType,prompt,log):
		"""Migrates this content to v2 adding it to the parent content node."""
		interaction=None
		if isinstance(self.parent,QTIResponseLId):
			if self.parent.rCardinality==QTIRCardinality.Ordered:
				raise QTIUnimplementedError("GraphicOrderInteraction")
			else:
				interaction=parent.ChildElement(qtiv2.QTIHotspotInteraction)
		elif isinstance(self.parent,QTIResponseXY):
			if self.parent.rCardinality==QTIRCardinality.Ordered:
				raise QTIUnimplementedError('response_xy x render_hotspot')
			else:
				interaction=parent.ChildElement(qtiv2.QTISelectPointInteraction)
		else:
			raise QTIUnimplementedError("%s x render_hotspot"%self.parent.__class__.__name__)
		if self.showDraw:
			log.append('Warning: ignoring showdraw="Yes", what did you really want to happen?')
		if self.minNumber is not None:
			interaction.minChoices=self.minNumber
		if self.maxNumber is not None:
			interaction.maxChoices=self.maxNumber
		labels=[]
		self.FindChildren(QTIResponseLabel,labels)
		# prompt is either a single <img> tag we already migrated or.. a set of inline
		# objects that are still to be migrated (and which should contain the hotspot image).
		img=None
		interactionPrompt=None
		hotspotImage=interaction.ChildElement(html.Object,(qtiv2.IMSQTI_NAMESPACE,'object'))
		if prompt:
			if not isinstance(prompt[0],html.Img):					
				interactionPrompt=interaction.ChildElement(qtiv2.QTIPrompt)
				for child in prompt:
					child.MigrateV2Content(interactionPrompt,html.InlineMixin,log)
				prompt=[]
				interactionPrompt.FindChildren(html.Img,prompt,1)				
		if prompt:
			# now the prompt should be a list containing a single image to use as the hotspot
			img=prompt[0]
			hotspotImage.data=img.src
			hotspotImage.height=img.height
			hotspotImage.width=img.width
			if img.src:
				# Annoyingly, Img throws away mime-type information from matimage
				images=[]
				self.parent.FindChildren(QTIMatImage,images,1)
				if images and images[0].uri:
					# Check that this is the right image in case img was embedded in QTIMatText
					if str(images[0].ResolveURI(images[0].uri))==str(img.ResolveURI(img.src)):
						hotspotImage.type=images[0].imageType
			for child in labels:
				if isinstance(child,QTIResponseLabel):
					child.MigrateV2HotspotChoice(interaction,log)
			return [interaction]
		else:
			# tricky, let's start by getting all the matimage elements in the presentation
			images=[]
			presentation=self.FindParent(QTIPresentation)
			if presentation:
				presentation.FindChildren(QTIMatImage,images)
			hsi=[]
			if len(images)==1:
				# Single image that must have gone AWOL
				hsi.append((images[0],labels))
			else:
				# multiple images are scanned for those at fixed positions in the presentation
				# which are hit by a hotspot (interpreted relative to the presentation).
				for img in images:
					hits=[]
					for child in labels:
						if child.HotspotInImage(img):
							hits.append(child)
					if hits:
						# So some of our hotspots hit this image
						hsi.append((img,hits))
			if len(hsi)==0:	
				log.append("Error: omitting render_hotspot with no hotspot image")
				return []
			else:
				img,hits=hsi[0]
				hotspotImage.data=img.ResolveURI(img.uri)
				hotspotImage.type=img.imageType
				hotspotImage.height=html.LengthType(img.height)
				hotspotImage.width=html.LengthType(img.width)
				# it will get cleaned up later
				if len(hsi)>0:
					# Worst case: multiple images => multiple hotspot interactions
					if self.maxNumber is not None:
						log.append("Warning: multi-image hotspot maps to multiple interactions, maxChoices can no longer be enforced")
					interaction.minChoices=None
					for child in hits:
						child.MigrateV2HotspotChoice(interaction,log,img.x0,img.y0)
					interactionList=[interaction]
					for img,hits in hsi[1:]:
						interaction=parent.ChildElement(qtiv2.QTIHotspotInteraction)
						if self.maxNumber is not None:
							interaction.maxChoices=self.maxNumber
						hotspotImage=interaction.ChildElement(html.Object,(qtiv2.IMSQTI_NAMESPACE,'object'))
						hotspotImage.data=img.ResolveURI(img.uri)
						hotspotImage.type=img.imageType
						hotspotImage.height=html.LengthType(img.height)
						hotspotImage.width=html.LengthType(img.width)
						for child in hits:
							child.MigrateV2HotspotChoice(interaction,log,img.x0,img.y0)
						interactionList.append(interaction)
					return interactionList
				else:
					# Best case: single image that just went AWOL
					for child in labels:
						child.MigrateV2HotspotChoice(interaction,log,img.x0,img.y0)
					return [interaction]


class QTIRenderSlider(QTIRenderThing):
	"""Represents the render_slider element.
	
::

	<!ELEMENT render_slider ((material | material_ref | response_label | flow_label)* , response_na?)>
	
	<!ATTLIST render_slider  orientation  (Horizontal | Vertical )  'Horizontal'
							  lowerbound  CDATA  #REQUIRED
							  upperbound  CDATA  #REQUIRED
							  step        CDATA  #IMPLIED
							  startval    CDATA  #IMPLIED
							  steplabel    (Yes | No )  'No'
							  %I_MaxNumber;
							  %I_MinNumber; >
	"""
	XMLNAME='render_slider'
	XMLATTR_orientation=('orientation',DecodeOrientation,EncodeOrientation)
	XMLATTR_lowerbound=('lowerBound',ParseInteger,FormatInteger)
	XMLATTR_upperbound=('upperBound',ParseInteger,FormatInteger)
	XMLATTR_step=('step',ParseInteger,FormatInteger)
	XMLATTR_startval=('startVal',ParseInteger,FormatInteger)
	XMLATTR_steplabel=('stepLabel',ParseYesNo,FormatYesNo)
	XMLATTR_maxnumber=('maxNumber',ParseInteger,FormatInteger)
	XMLATTR_minnumber=('minNumber',ParseInteger,FormatInteger)
	XMLCONTENT=xml.XMLElementContent
		
	def __init__(self,parent):
		QTIRenderThing.__init__(self,parent)
		self.orientation=QTIOrientation.Horizontal
		self.lowerBound=None
		self.upperBound=None
		self.step=None
		self.startVal=None
		self.stepLabel=False
		self.minNumber=None
		self.maxNumber=None

	def IsInline(self):
		"""This always results in a block-like interaction."""
		return False

	def MigrateV2Interaction(self,parent,childType,prompt,log):
		"""Migrates this content to v2 adding it to the parent content node."""
		interaction=None
		labels=[]
		self.FindChildren(QTIResponseLabel,labels)
		if self.maxNumber is None:
			maxChoices=len(labels)
		else:
			maxChoices=self.maxNumber
		if isinstance(self.parent,QTIResponseLId):
			if self.parent.rCardinality==QTIRCardinality.Single:
				log.append("Warning: choice-slider replaced with choiceInteraction.slider")
				interaction=parent.ChildElement(qtiv2.QTIChoiceInteraction)
				interaction.styleClass='slider'
				interaction.minChoices=1
				interaction.maxChoices=1
			elif self.parent.rCardinality==QTIRCardinality.Ordered:
				log.append("Error: ordered-slider replaced with orderInteraction.slider")
				raise QTIUnimplementedError("OrderInteraction")
			else:
				log.append("Error: multiple-slider replaced with choiceInteraction.slider")
				interaction=parent.ChildElement(qtiv2.QTIChoiceInteraction)
				interaction.styleClass='slider'
				if self.minNumber is not None:
					interaction.minChoices=self.minNumber
				else:
					interaction.minChoices=maxChoices
				interaction.maxChoices=maxChoices
			interaction.shuffle=False
			for child in labels:
				child.MigrateV2SimpleChoice(interaction,log)
		elif isinstance(self.parent,QTIResponseNum):
			if self.parent.rCardinality==QTIRCardinality.Single:
				interaction=parent.ChildElement(qtiv2.SliderInteraction)
				interaction.lowerBound=float(self.lowerBound)
				interaction.upperBound=float(self.upperBound)
				if self.step is not None:
					interaction.step=self.step
				if self.orientation is not None:
					interaction.orientation=V2ORIENTATION_MAP[self.orientation]
				# startValues are handled below after the variable is declared
			else:
				raise QTIUnimplementedError("Multiple/Ordered SliderInteraction")
		else:	
			raise QTIUnimplementedError("%s x render_slider"%self.parent.__class__.__name__)
		if prompt:
			interactionPrompt=interaction.ChildElement(qtiv2.QTIPrompt)
			for child in prompt:
				child.MigrateV2Content(interactionPrompt,html.InlineMixin,log)			
		return [interaction]
		
	def MigrateV2InteractionDefault(self,declaration,interaction):
		# Most interactions do not need default values.
		if isinstance(interaction,qtiv2.SliderInteraction) and self.startVal is not None:
			value=declaration.ChildElement(qtiv2.QTIDefaultValue).ChildElement(qtiv2.QTIValue)
			if declaration.baseType==qtiv2.BaseType.integer:
				value.SetValue(xsi.EncodeInteger(self.startVal))
			elif declaration.baseType==qtiv2.BaseType.float:
				value.SetValue(xsi.EncodeFloat(self.startVal))
			else:
				# slider bound to something else?
				raise QTIError("Unexpected slider type for default: %s"%qtiv2.EncodeBaseType(declaration.baseType))


class QTIRenderFIB(QTIRenderThing):
	"""Represents the render_fib element.
	
::

	<!ELEMENT render_fib ((material | material_ref | response_label | flow_label)* , response_na?)>
	
	<!ATTLIST render_fib  encoding    CDATA  'UTF_8'
						   fibtype      (String | Integer | Decimal | Scientific )  'String'
						   rows        CDATA  #IMPLIED
						   maxchars    CDATA  #IMPLIED
						   prompt       (Box | Dashline | Asterisk | Underline )  #IMPLIED
						   columns     CDATA  #IMPLIED
						   %I_CharSet;
						   %I_MaxNumber;
						   %I_MinNumber; >
	"""
	XMLNAME='render_fib'
	XMLATTR_encoding='encoding'
	XMLATTR_fibtype=('fibType',DecodeFIBType,EncodeFIBType)
	XMLATTR_rows=('rows',ParseInteger,FormatInteger)
	XMLATTR_maxchars=('maxChars',ParseInteger,FormatInteger)
	XMLATTR_prompt=('prompt',DecodePromptType,EncodePromptType)
	XMLATTR_columns=('columns',ParseInteger,FormatInteger)
	XMLATTR_charset='charset'		
	XMLATTR_maxnumber=('maxNumber',ParseInteger,FormatInteger)
	XMLATTR_minnumber=('minNumber',ParseInteger,FormatInteger)
	XMLCONTENT=xml.XMLElementContent
		
	def __init__(self,parent):
		QTIRenderThing.__init__(self,parent)
		self.encoding='UTF_8'
		self.fibType=QTIFIBType.String
		self.rows=None
		self.maxChars=None
		self.prompt=None
		self.columns=None
		self.charset='ascii-us'
		self.minNumber=None
		self.maxNumber=None
		self.labels=[]
		
	def ContentChanged(self):
		self.labels=[]
		self.FindChildren(QTIResponseLabel,self.labels)

	def MixedModel(self):
		"""Indicates whether or not this FIB uses a mixed model or not.
		
		A mixed model means that render_fib is treated as a mixture of
		interaction and content elements.  In an unmixed model the render_fib is
		treated as a single block interaction with an optional prompt.
		
		If the render_fib contains content, followed by labels, then we treat
		it as a prompt + fib and return False
		
		If the render_fib contains a mixture of content and labels, then we
		return True
		
		If the render_fib contains no content at all we assume it needs to be
		mixed into the surrounding content and return True."""
		children=self.GetLabelContent()
		foundLabel=False
		foundContent=False
		for child in children:
			if isinstance(child,QTIResponseLabel):
				foundLabel=True
			elif foundLabel:
				# any content after the first label means mixed mode.
				return True
			else:
				foundContent=True
		return not foundContent
		
	def IsInline(self):
		if self.MixedModel():
			return QTIRenderThing.IsInline(self)
		else:
			return False
	
	def InlineFIBLabel(self):
		if self.rows is None or self.rows==1:
			return True
		else:
			return False

	def MigrateV2FIBLabel(self,label,parent,childType,log):
		if self.InlineFIBLabel() or childType is html.InlineMixin:
			interaction=parent.ChildElement(qtiv2.TextEntryInteraction)
		else:
			interaction=parent.ChildElement(qtiv2.ExtendedTextInteraction)
		if label.GetChildren():
			log.append("Warning: ignoring content in render_fib.response_label")

	def MigrateV2Interaction(self,parent,childType,prompt,log):
		if self.InlineFIBLabel() or childType is html.InlineMixin:
			interactionType=qtiv2.TextEntryInteraction
		else:
			interactionType=qtiv2.ExtendedTextInteraction
		interactionList=[]
		parent.FindChildren(interactionType,interactionList)
		iCount=len(interactionList)
		# now migrate this object
		QTIRenderThing.MigrateV2Content(self,parent,childType,log)
		interactionList=[]
		parent.FindChildren(interactionType,interactionList)
		# ignore any pre-existing interactions of this type
		interactionList=interactionList[iCount:]
		if self.parent.rCardinality==QTIRCardinality.Single and len(interactionList)>1:
			log.append("Warning: single response fib ignoring all but last <response_label>")
			for interaction in interactionList[:-1]:
				interaction.parent.DeleteChild(interaction)
			interactionList=interactionList[-1:]
		for interaction in interactionList:
			if self.maxChars is not None:
				interaction.expectedLength=self.maxChars
			elif self.rows is not None and self.columns is not None:
				interaction.expectedLength=self.rows*self.columns
			if interactionType is qtiv2.ExtendedTextInteraction:
				if self.rows is not None:
					interaction.expectedLines=self.rows
		return interactionList


class QTIResProcessing(QTICommentElement):
	"""Represents the resprocessing element.
	
::

	<!ELEMENT resprocessing (qticomment? , outcomes , (respcondition | itemproc_extension)+)>
	
	<!ATTLIST resprocessing  %I_ScoreModel; >
	"""
	XMLNAME='resprocessing'
	XMLATTR_scoremodel='scoreModel'
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTICommentElement.__init__(self,parent)
		self.scoreModel=None
		self.QTIOutcomes=QTIOutcomes(self)
		self.conditions=[]
		
	def QTIRespCondition(self):
		child=QTIRespCondition(self)
		self.conditions.append(child)
		return child
	
	def QTIItemProcExtension(self):
		child=QTIItemProcExtension(self)
		self.conditions.append(child)
		return child
	
	def GetChildren(self):
		children=QTICommentElement.GetChildren(self)
		children.append(self.QTIOutcomes)
		return children+self.conditions

	def MigrateV2(self,v2Item,log):
		"""Migrates v1 resprocessing to v2 ResponseProcessing."""
		rp=v2Item.ChildElement(qtiv2.QTIResponseProcessing)
		for outcomeFixup in sorted(self._interactionFixup.keys()):
			setValue=rp.ChildElement(qtiv2.QTISetOutcomeValue)
			setValue.identifier=outcomeFixup
			multi=setValue.ChildElement(qtiv2.QTIMultiple)
			for rID in self._interactionFixup[outcomeFixup]:
				var=multi.ChildElement(qtiv2.QTIVariable)
				var.identifier=rID
		self.QTIOutcomes.MigrateV2(v2Item,log)
		cMode=True;ruleContainer=rp
		for condition in self.conditions:
			cMode,ruleContainer=condition.MigrateV2Rule(cMode,ruleContainer,log)
		
		
class QTIOutcomes(QTICommentElement):
	"""Represents the outcomes element.
	
::

	<!ELEMENT outcomes (qticomment? , (decvar , interpretvar*)+)>
	
	The implementation of this element takes a liberty with the content model
	because, despite the formulation above, the link between variables and
	their interpretation is not related to the order of the elements within
	the outcomes element.  (An interpretation without a variable reference
	defaults to an interpretation of the default 'SCORE' outcome.)
	
	When we output this element we do the decvars first, followed by
	the interpretVars.
	"""
	XMLNAME='outcomes'
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTICommentElement.__init__(self,parent)
		self.QTIDecVar=[]
		self.QTIInterpretVar=[]
	
	def GetChildren(self):
		children=QTICommentElement.GetChildren(self)
		return children+self.QTIDecVar+self.QTIInterpretVar

	def MigrateV2(self,v2Item,log):
		for d in self.QTIDecVar:
			d.MigrateV2(v2Item,log)
		for i in self.QTIInterpretVar:
			i.MigrateV2(v2Item,log)

		
class QTIRespCondition(QTICommentElement):
	"""Represents the respcondition element.
	
::

	<!ELEMENT respcondition (qticomment? , conditionvar , setvar* , displayfeedback* , respcond_extension?)>
	
	<!ATTLIST respcondition  %I_Continue;
							  %I_Title; >
	"""
	XMLNAME='respcondition'
	XMLATTR_continue=('continueFlag',ParseYesNo,FormatYesNo)
	XMLATTR_title='title'
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTICommentElement.__init__(self,parent)
		self.continueFlag=False
		self.title=None
		self.QTIConditionVar=QTIConditionVar(self)
		self.QTISetVar=[]
		self.QTIDisplayFeedback=[]
		self.QTIRespCondExtension=None
	
	def GetChildren(self):
		children=QTICommentElement.GetChildren(self)
		children.append(self.QTIConditionVar)
		children=children+self.QTISetVar+self.QTIDisplayFeedback
		xml.OptionalAppend(children,self.QTIRespCondExtension)
		return children
	
	def MigrateV2Rule(self,cMode,ruleContainer,log):
		"""Converts a response condition into v2 response processing rules.
		
		This method contains some tricky logic to help implement the confusing
		'continue' attribute of response conditions.  The continue attribute
		is interpreted in the following way:
		
		True: regardless of whether or not the condition matches, carry on to
		evaluate the next expression.
		
		False: only evaluate the next expression if the condition fails.
		
		The incoming cMode tells us if the previous condition set continue mode
		(the default is False on the attribute but the algorithm starts with
		continue mode True as the first rule is always evaluated).
		
		The way the rules are implemented is best illustrated by example, where
		X(True) represents condition X with continue='Yes' etc:
		
		R1(True),R2(True|False) becomes...
		
		if R1.test:
			R1.rules
		if R2.test:
			R2.rules
		
		R1(False),R2(True) becomes...
		
		if R1.test:
			R1.rules
		else:
			if R2.test:
				R2.rules
		
		R1(False),R2(False) becomes...
		
		if R1.test:
			R1.rules
		elif R2.test:
			R2.rules
		"""
		if self.continueFlag:
			if not cMode:
				ruleContainer=ruleContainer.ChildElement(qtiv2.QTIResponseElse)
			rc=ruleContainer.ChildElement(qtiv2.QTIResponseCondition)
			rcIf=rc.ChildElement(qtiv2.QTIResponseIf)
		else:
			if cMode:
				rc=ruleContainer.ChildElement(qtiv2.QTIResponseCondition)
				ruleContainer=rc
				rcIf=rc.ChildElement(qtiv2.QTIResponseIf)
			else:
				rcIf=ruleContainer.ChildElement(qtiv2.QTIResponseElseIf)
		self.QTIConditionVar.MigrateV2Expression(rcIf,log)
		for rule in self.QTISetVar:
			rule.MigrateV2Rule(rcIf,log)
		for rule in self.QTIDisplayFeedback:
			rule.MigrateV2Rule(rcIf,log)
		return self.continueFlag,ruleContainer

		
class QTIItemFeedback(QTIElement,QTIViewMixin,QTIContentMixin):
	"""Represents the itemfeedback element.
	
::

	<!ELEMENT itemfeedback ((flow_mat | material) | solution | hint)+>
	
	<!ATTLIST itemfeedback  %I_View;
							 %I_Ident;
							 %I_Title; >
	"""
	XMLNAME='itemfeedback'
	XMLATTR_title='title'
	XMLATTR_ident='ident'		

	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		QTIViewMixin.__init__(self)
		QTIContentMixin.__init__(self)
		self.title=None
		self.ident=None

	def GetChildren(self):
		children=QTIElement.GetChildren(self)+self.contentChildren
		return children

	def QTIMaterial(self):
		child=QTIMaterial(self)
		self.contentChildren.append(child)
		return child
	
	def QTIFlowMat(self):
		child=QTIFlowMat(self)
		self.contentChildren.append(child)
		return child

	def QTISolution(self):
		child=QTISolution(self)
		self.contentChildren.append(child)
		return child

	def QTIHint(self):
		child=QTIHint(self)
		self.contentChildren.append(child)
		return child
		
	def MigrateV2(self,v2Item,log):
		feedback=v2Item.ChildElement(qtiv2.QTIModalFeedback)
		if not (self.view.lower()=='all' and self.view.lower()=='candidate'):
			log.append("Warning: discarding view on feedback (%s)"%self.view)
		identifier=qtiv2.ValidateIdentifier(self.ident,'FEEDBACK_')
		feedback.outcomeIdentifier='FEEDBACK'
		feedback.showHide=qtiv2.QTIShowHide.show
		feedback.identifier=identifier
		feedback.title=self.title
		QTIContentMixin.MigrateV2Content(self,feedback,html.FlowMixin,log)
			
		
class QTISolution(QTIContentMixin,QTICommentElement):
	"""Represents the solution element::

	<!ELEMENT solution (qticomment? , solutionmaterial+)>
	
	<!ATTLIST solution  %I_FeedbackStyle; >
	"""
	XMLNAME='solution'
	XMLATTR_feedbackstyle=('feedbackStyle',DecodeFeedbackStyle,EncodeFeedbackStyle)
	XMLCONTENT=xml.XMLElementContent

	def __init__(self,parent):
		QTICommentElement.__init__(self,parent)
		QTIContentMixin.__init__(self)
		self.feedbackStyle=QTIFeedbackStyle.Complete
	
	def GetChildren(self):
		return QTICommentElement.GetChildren()+self.contentChildren

	def QTISolutionMaterial(self):
		child=QTISolutionMaterial(self)
		self.contentChildren.append(child)
		return child
		

class QTIFeedbackMaterial(QTIContentMixin,QTIElement):
	"""Abstract class for solutionmaterial and hintmaterial::

	<!ELEMENT * (material+ | flow_mat+)>
	"""
	XMLCONTENT=xml.XMLElementContent
	
	def __init__(self,parent):
		QTIElement.__init__(self,parent)
		QTIContentMixin.__init__(self)

	def GetChildren(self):
		return self.contentChildren[:]

	def QTIMaterial(self):
		child=QTIMaterial(self)
		self.contentChildren.append(child)
		return child
	
	def QTIFlowMat(self):
		child=QTIFlowMat(self)
		self.contentChildren.append(child)
		return child
		
	
class QTISolutionMaterial(QTIFeedbackMaterial):
	"""Represents the solutionmaterial element::

	<!ELEMENT solutionmaterial (material+ | flow_mat+)>
	"""
	XMLNAME='solutionmaterial'


class QTIHint(QTICommentElement):
	"""Represents the hint element.
	
::

	<!ELEMENT hint (qticomment? , hintmaterial+)>
	
	<!ATTLIST hint  %I_FeedbackStyle; >
	"""
	XMLNAME='hint'
	XMLATTR_feedbackstyle=('feedbackStyle',DecodeFeedbackStyle,EncodeFeedbackStyle)
	XMLCONTENT=xml.XMLElementContent

	def __init__(self,parent):
		QTICommentElement.__init__(self,parent)
		QTIContentMixin.__init__(self)
		self.feedbackStyle=QTIFeedbackStyle.Complete
	
	def GetChildren(self):
		return QTICommentElement.GetChildren()+self.contentChildren
	
	def QTIHintMaterial(self):
		child=QTIHintMaterial(self)
		self.contentChildren.append(child)
		return child


class QTIHintMaterial(QTIFeedbackMaterial):
	"""Represents the hintmaterial element::

	<!ELEMENT hintmaterial (material+ | flow_mat+)>
	"""
	XMLNAME='hintmaterial'
	

#
#	SELECTION AND ORDERING OBJECT DEFINITIONS
#
class QTISelection(QTIElement):
	"""Represents the selection element.
	
::

	<!ELEMENT selection (sourcebank_ref? , selection_number? , selection_metadata? ,
		(and_selection | or_selection | not_selection | selection_extension)?)>
	"""
	XMLNAME='selection'
	XMLCONTENT=xml.XMLElementContent
	

class QTIOrder(QTIElement):
	"""Represents the order element.
	
::

	<!ELEMENT order (order_extension?)>
	
	<!ATTLIST order  order_type CDATA  #REQUIRED >
	"""
	XMLNAME='order'
	XMLCONTENT=xml.XMLElementContent
	

class QTISelectionNumber(QTIElement):
	"""Represents the selection_number element.
	
::

	<!ELEMENT selection_number (#PCDATA)>
	"""
	XMLNAME='selection_number'
	XMLCONTENT=xml.XMLMixedContent
	

class QTISelectionMetadata(QTIElement):
	"""Represents the selection_metadata element.
	
::

	<!ELEMENT selection_metadata (#PCDATA)>
	
	<!ATTLIST selection_metadata  %I_Mdname;
								   %I_Mdoperator; >
	"""
	XMLNAME='selection_metadata'
	XMLCONTENT=xml.XMLMixedContent
	

class QTISequenceParameter(QTIElement):
	"""Represents the sequence_parameter element.
	
::

	<!ELEMENT sequence_parameter (#PCDATA)>
	
	<!ATTLIST sequence_parameter  %I_Pname; >
	"""
	XMLNAME='sequence_parameter'
	XMLCONTENT=xml.XMLMixedContent
	

class QTISourcebankRef(QTIElement):
	"""Represents the sourcebank_ref element.
	
::

	<!ELEMENT sourcebank_ref (#PCDATA)>
	"""
	XMLNAME='sourcebank_ref'
	XMLCONTENT=xml.XMLMixedContent
	

class QTIAndSelection(QTIElement):
	"""Represents the and_selection element.
	
::

	<!ELEMENT and_selection (selection_metadata | and_selection | or_selection | not_selection)+>
	"""
	XMLNAME='and_selection'
	XMLCONTENT=xml.XMLElementContent
	

class QTIOrSelection(QTIElement):
	"""Represents the or_selection element.
	
::

	<!ELEMENT or_selection (selection_metadata | and_selection | or_selection | not_selection)+>
	"""
	XMLNAME='or_selection'
	XMLCONTENT=xml.XMLElementContent
	

class QTINotSelection(QTIElement):
	"""Represents the not_selection element.
	
::

	<!ELEMENT not_selection (selection_metadata | and_selection | or_selection | not_selection)>
	"""
	XMLNAME='not_selection'
	XMLCONTENT=xml.XMLElementContent
	

#
#	OUTCOMES PREOCESSING OBJECT DEFINITIONS
#
class QTIObjectsCondition(QTICommentElement):
	"""Represents the objects_condition element.
	
::

	<!ELEMENT objects_condition (qticomment? ,
		(outcomes_metadata | and_objects | or_objects | not_objects)? ,
		objects_parameter* , map_input* , objectscond_extension?)>
	"""
	XMLNAME='objects_condition'
	XMLCONTENT=xml.XMLElementContent
	

class QTIMapOutput(QTIElement):
	"""Represents the map_output element.
	
::

	<!ELEMENT map_output (#PCDATA)>
	
	<!ATTLIST map_output  %I_VarName; >
	"""
	XMLNAME='map_output'
	XMLCONTENT=xml.XMLMixedContent
	
	
class QTIMapInput(QTIElement):
	"""Represents the map_input element.
	
::

	<!ELEMENT map_input (#PCDATA)>
	
	<!ATTLIST map_input  %I_VarName; >
	"""
	XMLNAME='map_input'
	XMLCONTENT=xml.XMLMixedContent
	
	
class QTIOutcomesFeedbackTest(QTIElement):
	"""Represents the outcomes_feedback_test element.
	
::

	<!ELEMENT outcomes_feedback_test (test_variable , displayfeedback+)>

	<!ATTLIST outcomes_feedback_test  %I_Title; >
	"""
	XMLNAME='outcomes_feedback_test'
	XMLCONTENT=xml.XMLElementContent
	

class QTIOutcomesMetadata(QTIElement):
	"""Represents the outcomes_metadata element.
	
::

	<!ELEMENT outcomes_metadata (#PCDATA)>

	<!ATTLIST outcomes_metadata  %I_Mdname;
								  %I_Mdoperator; >
	"""
	XMLNAME='outcomes_metadata'
	XMLCONTENT=xml.XMLElementContent

	
class QTIAndObjects(QTIElement):
	"""Represents the and_objects element.
	
::

	<!ELEMENT and_objects (outcomes_metadata | and_objects | or_objects | not_objects)+>
	"""
	XMLNAME='and_objects'
	XMLCONTENT=xml.XMLElementContent
	

class QTIOrObjects(QTIElement):
	"""Represents the or_objects element.
	
::

	<!ELEMENT or_objects (outcomes_metadata | and_objects | or_objects | not_objects)+>
	"""
	XMLNAME='or_objects'
	XMLCONTENT=xml.XMLElementContent
	
	
class QTINotObjects(QTIElement):
	"""Represents the not_objects element.
	
::

	<!ELEMENT not_objects (outcomes_metadata | and_objects | or_objects | not_objects)>
	"""
	XMLNAME='not_objects'
	XMLCONTENT=xml.XMLElementContent
	
class QTITestVariable(QTIElement):
	"""Represents the test_variable element.
	
::

	<!ELEMENT test_variable (variable_test | and_test | or_test | not_test)>
	"""
	XMLNAME='test_variable'
	XMLCONTENT=xml.XMLElementContent

class QTIProcessingParameter(QTIElement):
	"""Represents the processing_parameter element.
	
::

	<!ELEMENT processing_parameter (#PCDATA)>

	<!ATTLIST processing_parameter  %I_Pname; >
	"""
	XMLNAME='processing_parameter'
	XMLCONTENT=xml.XMLMixedContent


class QTIAndTest(QTIElement):
	"""Represents the and_test element.
	
::

	<!ELEMENT and_test (variable_test | and_test | or_test | not_test)+>
	"""
	XMLNAME='and_test'
	XMLCONTENT=xml.XMLElementContent
	

class QTIOrTest(QTIElement):
	"""Represents the or_test element.
	
::

	<!ELEMENT or_test (variable_test | and_test | or_test | not_test)+>
	"""
	XMLNAME='or_test'
	XMLCONTENT=xml.XMLElementContent
	

class QTINotTest(QTIElement):
	"""Represents the not_test element.
	
::

	<!ELEMENT not_test (variable_test | and_test | or_test | not_test)>
	"""
	XMLNAME='not_test'
	XMLCONTENT=xml.XMLElementContent


class QTIVariableTest(QTIElement):
	"""Represents the variable_test element.
	
::

	<!ELEMENT variable_test (#PCDATA)>

	<!ATTLIST variable_test  %I_VarName;
                          %I_Testoperator; >
	"""
	XMLNAME='variable_test'
	XMLCONTENT=xml.XMLElementContent



class QTIObjectsParameter(QTIElement):
	"""Represents the objects_parameter element.
	
::

	<!ELEMENT objects_parameter (#PCDATA)>

	<!ATTLIST objects_parameter  %I_Pname; >
	"""
	XMLNAME='objects_parameter'
	XMLCONTENT=xml.XMLMixedContent


#
#	END OF SPECIFICATION ELEMENT DEFINITIONS
#

class QTIDocument(xml.XMLDocument):
	"""Class for working with QTI documents."""
	
	def __init__(self,**args):
		"""We turn off the parsing of external general entities to prevent a
		missing DTD causing the parse to fail.  This is a significant limitation
		as it is possible that some sophisticated users have used general
		entities to augment the specification or to define boiler-plate code. 
		If this causes problems then you can turn the setting back on again for
		specific instances of the parser that will be used with that type of
		data."""
		xml.XMLDocument.__init__(self,**args)
		self.material={}
		self.matThings={}
		
	classMap={}
	"""classMap is a mapping from element names to the class object that will be used to represent them."""
	
	def GetElementClass(self,name):
		"""Returns the class to use to represent an element with the given name.
		
		This method is used by the XML parser.  The class object is looked up in
		:py:attr:`classMap`, if no specialized class is found then the general
		:py:class:`pyslet.xml20081126.XMLElement` class is returned."""
		return QTIDocument.classMap.get(name,QTIDocument.classMap.get(None,xml.XMLElement))

	def RegisterMatThing(self,matThing):
		"""Registers a QTIMatThing instance in the dictionary of matThings."""
		if matThing.label is not None:
			self.matThings[matThing.label]=matThing
	
	def UnregisterMatThing(self,mathThing):
		if matThing.label is not None and matThing is self.matThings.get(matThing.label,None):
			del self.matThings[matThing.label]			
	
	def FindMatThing(self,linkRefID):
		return self.matThings.get(linkRefID,None)
	
	def MigrateV2(self,cp):
		"""Converts the contents of this document to QTI v2
		
		The output is stored into the content package passed in cp.  Errors and
		warnings generated by the migration process are added as annotations to
		the resulting resource objects in the content package.
		
		The function returns a list of 3-tuples, one for each object migrated.
		
		Each tuple comprises ( <QTI v2 Document>, <LOM Metadata>, <log> )"""
		if isinstance(self.root,QTIQuesTestInterop):
			results=self.root.MigrateV2()
			# list of tuples ( <QTIv2 Document>, <Metadata>, <Log Messages> )
			if results:
				# Make a directory to hold the files (makes it easier to find unique names for media files)
				if isinstance(self.baseURI,uri.FileURL):
					ignore,dName=os.path.split(self.baseURI.GetPathname())
				else:
					dName="questestinterop"
				dName,ext=os.path.splitext(dName)
				dName=cp.GetUniqueFile(dName)
				for doc,metadata,log in results:
					if log:
						# clean duplicate lines from the log then add as an annotation
						logCleaner={}
						i=0
						while i<len(log):
							if logCleaner.has_key(log[i]):
								del log[i]
							else:
								logCleaner[log[i]]=i
								i=i+1
						annotation=metadata.LOMAnnotation()
						annotationMsg=string.join(log,';\n')
						description=annotation.ChildElement(imsmd.LOMDescription)
						description.LangString(annotationMsg)
					doc.AddToContentPackage(cp,metadata,dName)
				cp.manifest.Update()
			return results
		else:
			return []

xml.MapClassElements(QTIDocument.classMap,globals())


try:
	CNBIG5=codecs.lookup('cn-big5')
	pass
except LookupError:
	CNBIG5=None
	try:
		BIG5=codecs.lookup('big5')
		CNBIG5=codecs.CodecInfo(BIG5.encode, BIG5.decode, streamreader=BIG5.streamreader,
			streamwriter=BIG5.streamwriter, incrementalencoder=BIG5.incrementalencoder,
			incrementaldecoder=BIG5.incrementaldecoder, name='cn-big5')
	except LookupError:
		# we'll have to do without cn-big5
		pass

try:
	APPLESYMBOL=codecs.lookup('apple-symbol')
	pass
except LookupError:
	import pyslet.unicode_apple_symbol as symbol
	APPLESYMBOL=symbol.getregentry()


def QTICodecSearch(name):
	if name.lower()=="cn-big5" and CNBIG5:
		return CNBIG5
	elif name.lower()=="apple-symbol":
		return APPLESYMBOL
	
def RegisterCodecs():
	"""The example files that are distributed with the QTI specification contain
	a set of Chinese examples encoded using big5.  However, the xml declarations
	on these files refer to the charset as "CN-BIG5" and this causes errors when
	parsing them as this is a non-standard way of refering to big5.
	
	QTI also requires use of the apple symbol font mapping for interpreting
	symbol-encoded maths text in questions."""
	codecs.register(QTICodecSearch)

# Force registration of codecs on module load
RegisterCodecs()

# Legacy function no longer needed
def FixupCNBig5(): pass
