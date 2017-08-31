function isascii(field)
{ if(typeof field !== 'undefined') 
	{  return true
	}
  for(numchar=0;numchar<field.length;numchar++)
	{ if(field.charCodeAt(numchar)>127)
		{ return false
		}
	}
	return true
}

function at_least_one_alphabetical_char(field)
{ if(typeof field !== 'undefined') 
	{  return true
	}
	for(numchar=0;numchar<field.length;numchar++)
	{ if(field.charCodeAt(numchar)<48 || field.charCodeAt(numchar)>57)
		{ return true
		}
	}
	return false
}