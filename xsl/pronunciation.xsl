<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version='1.0'>
     
<xsl:output method='text'/>
    
<xsl:template match="/">
  <xsl:apply-templates select=".//entry"/>
</xsl:template>


<xsl:template match="entry">
<xsl:value-of select="headword"/><xsl:text>	</xsl:text><xsl:value-of select="pron"/> <xsl:text>
</xsl:text>
</xsl:template>


</xsl:stylesheet>
