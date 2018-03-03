#!/usr/bin/env python
import os
import jinja2
import webapp2

from models import Sporocilo

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        return self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        return self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if params is None:
            params = {}
        template = jinja_env.get_template(view_filename)
        return self.response.out.write(template.render(params))


class MainHandler(BaseHandler):
    def get(self):
        return self.render_template("hello.html")


class RezultatHandler(BaseHandler):
    def post(self):
        rezultat = self.request.get("input-sporocilo")

        sporocilo = Sporocilo(besedilo=rezultat)
        sporocilo.put()
        return self.write(rezultat)


class ListHandler(BaseHandler):
    def get(self):
        # Iz baze vzamemo vsa sporocila, ki imajo polje izbrisano nastavljena na False
        seznam = Sporocilo.query(Sporocilo.izbrisano == False).fetch()
        params = {"seznam": seznam}
        return self.render_template("seznam.html", params=params)


class PosameznoSporociloHandler(BaseHandler):
    def get(self, sporocilo_id):
        # Iz baze vzamemo sporocilo, katerega id je enak podanemu
        sporocilo = Sporocilo.get_by_id(int(sporocilo_id))

        params = {"sporocilo": sporocilo}
        return self.render_template("posamezno_sporocilo.html", params=params)


class UrediHandler(BaseHandler):
    def get(self, sporocilo_id):
        # Ideja: vzamemo sporocilo iz baze
        sporocilo = Sporocilo.get_by_id(int(sporocilo_id))
        params = {"sporocilo": sporocilo}
        # In ga pokazemo
        return self.render_template("uredi_sporocilo.html", params=params)

    def post(self, sporocilo_id):
        # Vzamemo sporocilo iz baze
        sporocilo = Sporocilo.get_by_id(int(sporocilo_id))
        # sporocilo posodobimo
        sporocilo.besedilo = self.request.get("nov-text")
        # in ga shranimo nazaj v bazo
        sporocilo.put()
        # Uporabnika preusmerimo nazaj na seznam sporocil (po imenu)
        # Pomen preusmerjanja po imenu je v tem, da se lahko pot povezave spremeni
        # ime pa ostane enako in ne potrebuje ospreminjati poti na vec mestih
        self.redirect_to("seznam-sporocil")


# Dodatno:
# na strani https://stackoverflow.com/questions/6515502/javascript-form-submit-confirm-or-cancel-submission-dialog-box
# prvi ogovor pokaze kako lahko s pomocjo javascripta pokazemo potrditveno sporocilo
class IzbrisiHandler(BaseHandler):
    def get(self, sporocilo_id):
        # Vzamemo sporocilo ven
        sporocilo = Sporocilo.get_by_id(int(sporocilo_id))
        params = {"sporocilo": sporocilo}
        # Prikazemo potrditveno spletno stran
        # Ker si posljemo sporocilo, lahko pokazemo se kaksno informacijo o sporocilu
        return self.render_template("izbrisi.html", params=params)

    def post(self, sporocilo_id):
        sporocilo = Sporocilo.get_by_id(int(sporocilo_id))
        # Sporocila ne izbrisemo, ampak ga zgolj "skrijemo"
        sporocilo.izbrisano = True
        # In zapisemo nazaj v bazo
        sporocilo.put()
        self.redirect_to("seznam-sporocil")

app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler),
    webapp2.Route('/rezultat', RezultatHandler),
    # pot poimenujemo, da se lahko sklicemo nanjo ko preusmerimo uporabnika
    webapp2.Route('/seznam', ListHandler, name="seznam-sporocil"),
    # Na to pot primejo linki oblike /sporocilo/{{poljubne stevke}}
    # sporocilo_id pa je zgolj poimenovanje, ki ga potem uporabimo v metodi,
    # ki se klice ob prihodu na to pot
    webapp2.Route('/sporocilo/<sporocilo_id:\d+>', PosameznoSporociloHandler),
    webapp2.Route('/sporocilo/<sporocilo_id:\d+>/edit', UrediHandler),
    webapp2.Route('/sporocilo/<sporocilo_id:\d+>/delete', IzbrisiHandler)
], debug=True)
