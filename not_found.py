import httplib2
import os
import webapp2
import jinja2


# Set jinja Environment
template_env= jinja2.Environment(loader=jinja2.FileSystemLoader(os.getcwd()))


class NotFound(webapp2.RequestHandler):

    def get(self):
        
        template = template_env.get_template('/www/not_found.html')
        self.response.out.write(template.render()) 


app = webapp2.WSGIApplication([
    ('/.*', NotFound),
], debug=True)