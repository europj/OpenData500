from base import *
import json


#--------------------------------------------------------MAIN PAGE------------------------------------------------------------
class MainHandler(BaseHandler):
    @tornado.web.addslash
    #@tornado.web.authenticated
    def get(self, country=None):
        if not country:
            country = "us"
        if country not in available_countries:
            self.redirect("/404/")
            return
        with open("templates/"+country+"/settings.json") as json_file:
            settings = json.load(json_file)
        # lan = self.get_argument("lan", "")
        # if lan and lan != self.get_cookie("lan"):
        #     self.set_cookie("lan", lan)
        # if not lan:
        #     lan = self.get_cookie("lan")
        # if not lan: or lan not in settings["available_languages"]:
        #     lan = settings['default_language']
        #     self.set_cookie("lan", lan)
        lan = self.get_cookie("lan")
        if not lan:
            lan = settings['default_language']
        self.render(
            country.lower()+ "/" + lan + "/index.html",
            settings = settings,
            menu=settings['menu'][lan],
            user=self.current_user,
            lan = lan,
            country=country
        )

#--------------------------------------------------------TEST PAGE------------------------------------------------------------
class TestHandler(BaseHandler):
    @tornado.web.addslash
    #@tornado.web.authenticated
    def get(self, number):
        self.render(
            "index_" + number + ".html",
            user=self.current_user,
            page_title='Open Data500',
            page_heading='Welcome to the Open Data 500 Pre-Launch',
        )

#--------------------------------------------------------ROUNDATABLE PAGE------------------------------------------------------------
class RoundtableHandler(BaseHandler):
    @tornado.web.addslash
    #@tornado.web.authenticated
    def get(self, country, rt=None):
        if self.request.uri == "/roundtables/doc/":
            self.redirect("/us/roundtables/?rt=doc")
        if not country:
            self.redirect("/us/roundtables/")
            return
        rt = self.get_argument("rt", "main")
        with open("templates/us/settings.json") as json_file:
            settings = json.load(json_file)
        logging.info("Country: " + country + " RT: " + rt)
        self.render(
            "us/en/"+rt+"_roundtable.html",
            page_title = "Open Data Roundtables",
            page_heading = "Open Data Roundtables",
            user=self.current_user,
            country=country,
            settings=settings,
            menu=settings['menu']['en'],
            lan="en"
        )


#--------------------------------------------------------STATIC PAGE------------------------------------------------------------
class StaticPageHandler(BaseHandler):
    @tornado.web.addslash
    #@tornado.web.authenticated
    def get(self, country=None, page=None):
        #check if company page, get company if so
        try:
            company = models.Company.objects.get(Q(prettyName=page) & Q(display=True))
            if company.country != country:
                self.redirect("/" + company.country + "/" + company.prettyName + "/")
                return
        except DoesNotExist:
            company = None
        except MultipleObjectsReturned:
            company = models.Company.objects(Q(prettyName=page) & Q(country=country) & Q(display=True))[0]
            if company.country != country:
                self.redirect("/" + company.country + "/" + company.prettyName + "/")
                return
        except Exception, e:
            logging.info("Uncaught Exception: " + str(e))
            self.render(
                "500.html",
                page_title='500 - Server Error',
                user=self.current_user,
                page_heading='Uh oh... You broke it.',
                message = "I'm telling."
            )
            return
        #country, language, settings for page
        if not country:
            country = "us" #us default country
        if country not in available_countries:
            self.redirect("/404/")
            return
        with open("templates/"+country+"/settings.json") as json_file:
            settings = json.load(json_file)
        lan = self.get_cookie("lan")
        if not lan:
            lan = settings['default_language']
        if company: 
            self.render(
                company.country + "/" + lan + "/company.html",
                page_title=company.companyName,
                user=self.current_user,
                page_heading=company.companyName,
                company = company,
                menu=settings['menu'][lan],
                settings=settings,
                country=country,
                lan=lan
            )
            return
        else:
            try:
                page_title=settings['page_titles'][lan][page]
            except:
                page_title="OD500"
            try: 
                self.render(
                    country + "/" + lan + "/" + page + ".html",
                    user=self.current_user,
                    country=country,
                    menu=settings['menu'][lan],
                    settings=settings,
                    page_title=page_title,
                    lan=lan
                )
                return
            except Exception, e:
                self.render(country + "/" + lan + '/404.html',
                    user=self.current_user,
                    country=country,
                    page_title=page_title,
                    menu=settings['menu'][lan],
                    settings=settings,
                    lan=lan,
                    error=e
                )
                return



#--------------------------------------------------------FULL LIST PAGE------------------------------------------------------------
class ListHandler(BaseHandler):
    @tornado.web.addslash
    #@tornado.web.authenticated
    def get(self, country=None, name=None):
        if name == "candidates":
            self.redirect("/us/list/")
            return 
        if not country:
            country = "us"
        if country not in available_countries:
            self.redirect("/404/")
            return
        with open("templates/"+country+"/settings.json") as json_file:
                settings = json.load(json_file)
        lan = self.get_cookie("lan")
        if not lan:
            lan = settings['default_language']
        companies = models.Company.objects(Q(display=True) & Q(country=country)).order_by('prettyName')
        agencies = models.Agency.objects(Q(usedBy__not__size=0) & Q(source="dataGov") & Q(dataType="Federal")).order_by("-usedBy_count").only("name", "abbrev", "prettyName")[0:16]
        stats = models.Stats.objects().first()
        try:
            page_title=settings['page_titles'][lan]["list"]
        except:
            page_title="OD500"
        self.render(
            country+"/" + lan + "/list.html",
            companies = companies,
            stats = stats,
            states = states,
            agencies = agencies,
            categories = categories,
            user = self.current_user,
            country = country,
            menu=settings['menu'][lan],
            page_title=page_title,
            settings=settings,
            lan=lan
        )

#--------------------------------------------------------CHART PAGE------------------------------------------------------------
class ChartHandler(BaseHandler):
    @tornado.web.addslash
    def get(self):
        #log visit
        try: 
            visit = models.Visit()
            if self.request.headers.get('Referer'):
                visit.r = self.request.headers.get('Referer')
                logging.info("Chart requested from: " + self.request.headers.get('Referer'))
            else:
                visit.r = ''
                logging.info("Chart requested from: Cannot get referer")
            visit.p = "/chart/"
            visit.ua = self.request.headers.get('User-Agent')
            visit.ip = self.request.headers.get('X-Forwarded-For', self.request.headers.get('X-Real-Ip', self.request.remote_ip))
            if visit.r != "http://www.opendata500.com/" or visit.r != "http://www.opendata500.com":
                visit.save()
        except Exception, e:
            logging.info("Could not save visit information: " + str(e))
        finally:
            self.render("solo_chart.html")


#--------------------------------------------------------VALIDATE COMPANY EXISTS PAGE------------------------------------------------------------
#------SHOULD MOVE TO UTILS-------
class ValidateHandler(BaseHandler):
    def post(self):
        #check if companyName exists:
        country = self.get_argument("country", None)
        if country == "int":
            country = 'us'
        companyName = self.get_argument("companyName", None)
        prettyName = re.sub(r'([^\s\w])+', '', companyName).replace(" ", "-").title()
        try: 
            c = models.Company.objects.get(Q(country=country) & Q(prettyName=prettyName))
            logging.info('company exists.')
            self.write('{ "error": "This company has already been submitted. Email opendata500@thegovlab.org for questions." }')
        except:
            logging.info('company does not exist. Carry on.')
            self.write('true')

#--------------------------------------------------------SURVEY PAGE------------------------------------------------------------
class SubmitCompanyHandler(BaseHandler):
    @tornado.web.addslash
    #@tornado.web.authenticated
    def get(self, country=None):
        if not country:
            country = "us"
        if country not in available_countries:
            self.redirect("/404/")
            return
        with open("templates/"+country+"/settings.json") as json_file:
                settings = json.load(json_file)
        lan = self.get_cookie("lan")
        if not lan:
            lan = settings['default_language']
        try:
            page_title=settings['page_titles'][lan]["submit"]
        except:
            page_title="OD500"
        self.render(
            country+ "/" + lan + "/submitCompany.html",
            page_title = page_title,
            country=country,
            country_keys=country_keys,
            companyType = companyType,
            companyFunction = companyFunction,
            criticalDataTypes = criticalDataTypes,
            revenueSource = revenueSource,
            categories=categories,
            datatypes = datatypes,
            stateList = stateList,
            user=self.current_user,
            menu=settings['menu'][lan],
            stateListAbbrev=stateListAbbrev,
            settings=settings,
            lan=lan
        )

    #@tornado.web.authenticated
    def post(self, country=None):
        #print all arguments to log:
        logging.info("Submitting New Company")
        logging.info(self.request.arguments)
        if not country:
            country = "us"
        #-------------------CONTACT INFO---------------
        firstName = self.get_argument("firstName", None)
        lastName = self.get_argument("lastName", None)
        title = self.get_argument("title", None)
        email = self.get_argument("email", None)
        phone = self.get_argument("phone", None)
        try:
            if self.request.arguments['contacted']:
                contacted = True
        except:
            contacted = False
        contact = models.Person2(
            firstName = firstName,
            lastName = lastName,
            title = title,
            email = email,
            phone = phone,
            contacted = contacted,
        )
        #-------------------CEO INFO---------------
        ceoFirstName = self.get_argument("ceoFirstName", None)
        ceoLastName = self.get_argument("ceoLastName", None)
        ceo = models.Person2(
                firstName = ceoFirstName,
                lastName = ceoLastName,
                title = "CEO"
            )
        #-------------------COMPANY INFO---------------
        url = self.get_argument('url', None)
        companyName = self.get_argument("companyName", None)
        prettyName = re.sub(r'([^\s\w])+', '', companyName).replace(" ", "-").title()
        city = self.get_argument("city", None)
        zipCode = self.get_argument("zipCode", None)
        state = self.get_argument('state', None)
        companyType = self.get_argument("companyType", None)
        if companyType == 'other':
            companyType = self.get_argument('otherCompanyType', None)
        yearFounded = self.get_argument("yearFounded", None)
        if not yearFounded:
            yearFounded = 0
        fte = self.get_argument("fte", None).replace(",","")
        if not fte:
            fte = 0
        try:
            revenueSource = self.request.arguments['revenueSource']
        except:
            revenueSource = []
        if 'Other' in revenueSource:
            del revenueSource[revenueSource.index('Other')]
            revenueSource.append(self.get_argument('otherRevenueSource', None))
        companyCategory = self.get_argument("category", None)
        if companyCategory == 'Other':
            companyCategory = self.get_argument('otherCategory', None)
        description = self.get_argument('description', None)
        descriptionShort = self.get_argument('descriptionShort', None)
        financialInfo = self.get_argument('financialInfo')
        datasetWishList = self.get_argument('datasetWishList', None)
        sourceCount = self.get_argument("sourceCount", None)
        filters = [companyCategory, state, "survey-company"]
        #--SAVE COMPANY--
        company = models.Company(
            companyName = companyName,
            prettyName = prettyName,
            url = url,
            ceo = ceo,
            city = city,
            zipCode = zipCode,
            state=state,
            yearFounded = yearFounded,
            fte = fte,
            companyType = companyType,
            revenueSource = revenueSource,
            companyCategory = companyCategory,
            description= description,
            descriptionShort = descriptionShort,
            financialInfo = financialInfo,
            datasetWishList = datasetWishList,
            sourceCount = sourceCount,
            contact = contact,
            lastUpdated = datetime.now(),
            display = False, 
            submittedSurvey = True,
            vetted = False, 
            vettedByCompany = True,
            submittedThroughWebsite = True,
            locked=False,
            filters = filters,
            country=country
        )
        company.save()
        self.application.stats.update_all_state_counts(country)
        id = str(company.id)
        self.write({"id": id})


#--------------------------------------------------------DATA SUBMIT PAGE------------------------------------------------------------
class SubmitDataHandler(BaseHandler):
    @tornado.web.addslash
    #@tornado.web.authenticated
    def get(self, country, id):
        if not country:
            country = "us"
        if country not in available_countries:
            self.redirect("/404/")
            return
        with open("templates/"+country+"/settings.json") as json_file:
                settings = json.load(json_file)
        lan = self.get_argument("lan", "")
        if not lan or lan not in settings["available_languages"]:
            lan = settings["default_language"]
        company = models.Company.objects.get(id=bson.objectid.ObjectId(id))
        if company.country != country:
            self.redirect(str('/'+company.country+'/addData/'+id))
            return
        try:
            page_title=settings['page_titles'][lan]["submitData"]
        except:
            page_title="Submit Agency and Data Information"
        self.render(company.country + "/" + lan + "/submitData.html",
            page_title = page_title,
            page_heading = "Agency and Data Information for " + company.companyName,
            company = company,
            menu=settings['menu'][lan],
            user=self.current_user
        )

    #@tornado.web.authenticated
    def post(self, country, id):
        logging.info("Submitting Data: "+ self.get_argument("action", None))
        logging.info(self.request.arguments)
        try:
            company = models.Company.objects.get(id=bson.objectid.ObjectId(id))
        except Exception, e:
            logging.info("Could not get company: " + str(e))
            self.set_status(400)
        country = company.country
        with open("templates/"+country+"/settings.json") as json_file:
                settings = json.load(json_file)
        lan = self.get_cookie("lan")
        if not lan:
            lan = settings['default_language']
        agencyName = self.get_argument("agency", None)
        a_id = self.get_argument("a_id", None)
        subagencyName = self.get_argument("subagency", None)
        action = self.get_argument("action", None)
        #------------------------------------JUST SAVE DATA COMMENT QUESTION------------------------
        if action == "dataComments":
            logging.info("saving " + self.get_argument('dataComments', None))
            company.dataComments = self.get_argument('dataComments', None)
            company.lastUpdated = datetime.now()
            company.save()
            self.write({"result":"success", "redirect":"/"+ country + "/thanks/?lan=" + lan})
        #------------------------------------ADDING AGENCY/SUBAGENCY------------------------
        if action == "add agency":
            #Existing AGENCY
            logging.info("Trying to get: " + agencyName)
            try:
                agency = models.Agency.objects.get(Q(name=agencyName) & Q(country=company.country))
            except Exception, e:
                logging.info("Error: " + str(e))
                self.set_status(400)
            for s in agency.subagencies:
                if s.name == subagencyName:
                    if company not in s.usedBy: #only add if it's not already there.
                        s.usedBy.append(company)
            agency.save()
            if company not in agency.usedBy: #only add if it's not already there.
                agency.usedBy.append(company)
                agency.usedBy_count = len(agency.usedBy)
                agency.save()
            if agency not in company.agencies: #only add if it's not already there.
                company.agencies.append(agency)
            if agency.prettyName not in company.filters:
                company.filters.append(agency.prettyName)
                company.save()
            company.lastUpdated = datetime.now() #Update Company's Time of Last Edit
            company.save()
            self.write("success")
        #------------------------------------DELETING AGENCY/SUBAGENCY------------------------
        if action == "delete agency":
            try: 
                agency = models.Agency.objects.get(id=bson.objectid.ObjectId(a_id))
            except Exception, e:
                logging.info("Can't Delete Agency(search by ID): " + str(e))
                try:
                    agency = models.Agency.objects.get(name=agencyName)
                except Exception, e:
                    logging.info("Can't Delete Agency(Search by name): "+str(e))
                    self.set_status(400)
            if subagencyName == '': #delete from agency and subagency
                #remove datasets from agency:
                temp = []
                for d in agency.datasets:
                    if company != d.usedBy:
                        temp.append(d)
                    agency.datasets = temp
                #remove agency from company
                if agency in company.agencies:
                    company.agencies.remove(agency)
                if agency.prettyName in company.filters: #remove from list of filters
                    company.filters.remove(agency.prettyName)
                #remove company from agency
                if company in agency.usedBy:
                    agency.usedBy.remove(company)
                #remove datasets from subagencies
                for s in agency.subagencies:
                    if company in s.usedBy: #does the company even use this subagency?
                        temp = []
                        for d in s.datasets: #loop through all datasets for each subagency
                            if company != d.usedBy: #to make an array of the datasets not used by company
                                temp.append(d)
                        s.datasets = temp #and then set the datasets array equal to the remaining.
                        s.usedBy.remove(company)
                #remove from all subagencies
                for s in agency.subagencies:
                    if company in s.usedBy and s.name == subagencyName:
                        s.usedBy.remove(company)
            if subagencyName: #removing just subagency
                #remove datasets from subagency:
                temp = []
                for s in agency.subagencies:
                    if s.name == subagencyName:
                        for d in s.datasets:
                            if company != d.usedBy:
                                temp.append(d)
                        s.datasets = temp
                        #s.usedBy.remove(company)
                #remove company from specific subagency
                for s in agency.subagencies:
                    if company in s.usedBy and s.name == subagencyName:
                        s.usedBy.remove(company)
            agency.usedBy_count = len(agency.usedBy)
            agency.save()
            company.lastUpdated = datetime.now() #Update Company's Time of Last Edit
            company.save()
            self.write("deleted")
        #------------------------------------ADDING DATASET------------------------
        if action == "add dataset":
            try:
                agency = models.Agency.objects.get(Q(name = agencyName) & Q(country = company.country))
                logging.info(agency.name)
            except Exception, e:
                logging.info(str(e))
                logging.info("Agency Id: " + agencyName)
                self.set_status(500)
            datasetName = self.get_argument("datasetName", None)
            datasetURL = self.get_argument("datasetURL", None)
            try: 
                rating = int(self.get_argument("rating", None))
            except:
                rating = 0
            dataset = models.Dataset(
                datasetName = datasetName,
                datasetURL = datasetURL,
                rating = rating,
                usedBy = company)
            #Adding to agency or subagency?
            if subagencyName == '':
                #Add to Agency
                agency.datasets.append(dataset)
            else:
                #add to subagency
                for s in agency.subagencies:
                    if subagencyName == s.name:
                        s.datasets.append(dataset)
            agency.save()
            company.lastUpdated = datetime.now() #Update Company's Time of Last Edit
            company.save()
            self.write("success")
        #------------------------------------EDITING DATASET------------------------
        if action == "edit dataset":
            try:
                agency = models.Agency.objects.get(Q(name = agencyName) & Q(country = company.country))
            except:
                self.set_status(400)
            datasetName = self.get_argument("datasetName", None)
            previousDatasetName = self.get_argument("previousDatasetName", None)
            datasetURL = self.get_argument("datasetURL", None)
            try: 
                rating = int(self.get_argument("rating", None))
            except:
                rating = 0
            #-- At Agency Level?--
            if subagencyName == '':
                #find dataset:
                for d in agency.datasets:
                    if d.datasetName == previousDatasetName:
                        d.datasetName = datasetName
                        d.datasetURL = datasetURL
                        d.rating = rating
            else: #look for dataset in subagencies
                for s in agency.subagencies:
                    if s.name == subagencyName:
                        for d in s.datasets:
                            if d.datasetName == previousDatasetName:
                                d.datasetName = datasetName
                                d.datasetURL = datasetURL
                                d.rating = rating
            agency.save()
            company.lastUpdated = datetime.now() #Update Company's Time of Last Edit
            company.save()
            self.write("success")
        #------------------------------------DELETING DATASET------------------------
        if action == "delete dataset":
            try:
                agency = models.Agency.objects.get(Q(name = agencyName) & Q(country = company.country))
            except:
                self.set_status(400)
            datasetName = self.get_argument("datasetName", None)
            #Find dataset
            #--At Agency level?--
            if subagencyName == '':
                for d in agency.datasets:
                    if d.datasetName == datasetName:
                        agency.datasets.remove(d)
            else: #--SUBAGENCY LEVEL--
                for s in agency.subagencies:
                    if s.name == subagencyName:
                        for d in s.datasets:
                            if d.datasetName == datasetName:
                                s.datasets.remove(d)
            agency.save()
            company.lastUpdated = datetime.now() #Update Company's Time of Last Edit
            company.save()
            self.write("success")


#--------------------------------------------------------EDIT COMPANY PAGE------------------------------------------------------------
class EditCompanyHandler(BaseHandler):
    @tornado.web.addslash
    def get(self, country, id):
        try: 
            company = models.Company.objects.get(id=bson.objectid.ObjectId(id))
        except:
            self.render("404.html", 
                page_title = "That ain't even a thing.",
                page_heading = "Check yo'self",
                error = "404 - Not Found",
                user=self.current_user,
                message=id)
        if company.country != country:
            self.redirect(str('/'+company.country+'/edit/'+id))
            return
        with open("templates/"+company.country+"/settings.json") as json_file:
            settings = json.load(json_file)
        lan = self.get_cookie("lan")
        if not lan:
            lan = settings['default_language']
        if company.locked:
            self.render(company.country + "/404.html",
                page_title = "Can't Edit This Company",
                settings = settings[lan]['error']["locked"])
        else:
            self.render(company.country + "/editCompany.html",
                company = company,
                companyType = companyType,
                companyFunction = companyFunction,
                criticalDataTypes = criticalDataTypes,
                revenueSource = revenueSource,
                categories=categories,
                datatypes = datatypes,
                stateList = stateList,
                stateListAbbrev=stateListAbbrev,
                user=self.current_user,
                country = company.country,
                country_keys=country_keys,
                settings = settings[lan]['edit_company'],
                menu=settings['menu'][lan],
                id = str(company.id)
            )

    def post(self, country, id):
        #save all data to log:
        logging.info("Editing company:")
        logging.info(self.request.arguments)
        #get the company you will be editing
        company = models.Company.objects.get(id=bson.objectid.ObjectId(id))
        #------------------CONTACT INFO-------------------
        company.contact.firstName = self.get_argument("firstName", None)
        company.contact.lastName = self.get_argument("lastName", None)
        company.contact.title = self.get_argument("title", None)
        company.contact.org = self.get_argument("org", None)
        company.contact.email = self.get_argument("email", None)
        company.contact.phone = self.get_argument("phone", None)
        try: 
            if self.request.arguments['contacted']:
                company.contact.contacted = True
        except:
            company.contact.contacted = False
        #------------------CEO INFO-------------------
        company.ceo.firstName = self.get_argument("ceoFirstName", None)
        company.ceo.lastName = self.get_argument("ceoLastName", None)
        #------------------COMPANY INFO-------------------
        #company.companyName = self.get_argument("companyName", None)
        #company.prettyName = re.sub(r'([^\s\w])+', '', company.companyName).replace(" ", "-").title()
        company.url = self.get_argument('url', None)
        company.city = self.get_argument('city', None)
        company.state = self.get_argument('state', None)
        company.zipCode = self.get_argument('zipCode', None)
        company.companyType = self.get_argument("companyType", None)
        if company.companyType == 'other': #if user entered custom option for Type
            company.companyType = self.get_argument('otherCompanyType', None)
        company.yearFounded = self.get_argument("yearFounded", 0)
        if  not company.yearFounded:
            company.yearFounded = 0
        company.fte = self.get_argument("fte", 0)
        if not company.fte:
            company.fte = 0
        company.companyCategory = self.get_argument("category", None)
        if company.companyCategory == "Other":
            company.companyCategory = self.get_argument("otherCategory", None)
        try: #try and get all checked items. 
            company.revenueSource = self.request.arguments['revenueSource']
        except: #if no checked items, then make it into an empty array (form validation should prevent this always)
            company.revenueSource = []
        if 'Other' in company.revenueSource: #if user entered a custom option for Revenue Source
            del company.revenueSource[company.revenueSource.index('Other')] #delete 'Other' from list
            if self.get_argument('otherRevenueSource', None):
                company.revenueSource.append(self.get_argument('otherRevenueSource', None)) #add custom option to list.
        company.description = self.get_argument('description', None)
        company.descriptionShort = self.get_argument('descriptionShort', None)
        company.financialInfo = self.get_argument('financialInfo', None)
        company.datasetWishList = self.get_argument('datasetWishList', None)
        company.sourceCount = self.get_argument('sourceCount', None) 
        company.dataComments = self.get_argument("dataComments", None)
        company.datasetComments = self.get_argument('datasetComments', None)
        company.submittedSurvey = True
        company.vettedByCompany = True
        company.lastUpdated = datetime.now()
        company.filters = [company.companyCategory, company.state, "survey-company"] #re-do filters
        for a in company.agencies:
                if a.prettyName:
                    company.filters.append(a.prettyName)
        if company.display: #only if company is displayed
            self.application.stats.update_all_state_counts(company.country)
        company.save()
        #self.application.stats.update_all_state_counts()
        self.write('success')





