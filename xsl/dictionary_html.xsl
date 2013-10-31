<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version='1.0'>
     
<xsl:template match="/">
    <html>
      <head>
	<title>Australian Learner's Dictionary</title>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
	<style>
 	  .pronunciation { color: red; text-decoration: none; }
	  .example { color: green; text-decoration: none; }
	  .note { color: green; text-decoration: none; }
	</style>
      </head>

      <body>
	<xsl:apply-templates/>
      </body>
    </html>
</xsl:template>


<xsl:template match="entry">
    <p>
      <xsl:apply-templates/>
    </p>
</xsl:template>

<xsl:template match="headword">
    <b>
      <xsl:apply-templates/>
    </b>
</xsl:template>


<xsl:template match="form">
      <p><b><xsl:value-of select="@number"/></b> <xsl:apply-templates/></p>
</xsl:template>


<xsl:template match="pron">
	<span class="pronunciation">/<xsl:apply-templates/>/</span>
</xsl:template>

<xsl:template match="pluralform">
    (<i>plural forms </i> <b> <xsl:apply-templates/></b>)
</xsl:template>

<xsl:template match="verbform">
    (<i>verb forms </i> <b> <xsl:apply-templates/></b>)
</xsl:template>

<xsl:template match="pos">
    <i>
      <xsl:apply-templates/>
    </i>
</xsl:template>


<xsl:template match="definition">
    <xsl:apply-templates/>	
</xsl:template>

<xsl:template match="example">
    <a href="zyx.wav" class="example">
      <xsl:apply-templates/>
    </a>
</xsl:template>

<xsl:template match="italic">
    <i>
      <xsl:apply-templates/>
    </i>
</xsl:template>

<xsl:template match="bold">
    <b>
      <xsl:apply-templates/>
    </b>
</xsl:template>



<xsl:template match="note">
      <hr/>
      <p class="note"><xsl:apply-templates/></p>
      <hr/>
</xsl:template>





</xsl:stylesheet>
