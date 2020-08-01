from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.select import Select
import csv
import copy

class Lense:
    def __init__(self, _name, _perPackage, _price, _reviewCnt, _bc, _dia, _pwr,  _url, _productImage, _demonstrationImage):
        self.name = _name
        self.perPackage = _perPackage
        self.price = _price
        self.reviewCnt = _reviewCnt 
        self.bc = _bc
        self.dia = _dia
        self.pwr = _pwr
        self.url = _url
        self.productImage = _productImage
        self.demonstrationImage = _demonstrationImage

    def print(self):
        print(\
            "\
                name : %s\n\
                perPackage : %s\n\
                price : %s\n\
                reviewCnt : %s\n\
                bc : %s\n\
                dia : %s\n\
                pwr : %s\n\
                url : %s\n\
                productImage : %s\n\
                demonstrationImage : %s\n\
            "
            % (\
            self.name,\
            self.perPackage,\
            self.price,\
            self.reviewCnt,\
            self.bc,\
            self.dia,\
            self.pwr,\
            self.url,\
            self.productImage,\
            self.demonstrationImage\
            )
        )

class LenseShelf:
    def __init__(self, browser):
        self.driver = browser
        self.lenses = []

    def getLenses(self):
        self.driver.get("https://www.lensgogo.com/product-category/%ec%bd%98%ed%83%9d%ed%8a%b8%eb%a0%8c%ec%a6%88/")
        sleep(1)
        productPageURL= []
        while True:
            sleep(1)
            product_tiles = self.driver.find_elements_by_class_name("box-image")
            for tile in product_tiles:
                productPageURL.append(tile.find_element_by_tag_name("a").get_attribute("href"))
                # break #@For Test
            try:
                pagination = self.driver.find_element_by_class_name("next")
                pagination.click()
            except:
                break
        for productpage in productPageURL:
            self.getLense(productpage)
        self.exportLenses()        

    def removeStr(self, source, target):
        targetStart = source.find(target)
        if targetStart == -1:
            return source
        targetEnd = targetStart + len(target)
        return source[:targetStart] + source[targetEnd:]
    
    def removeUsage(self, name):
        closer = "개월용"
        idxCloser = name.find(closer)
        if idxCloser != -1:
            name = name[0:idxCloser-2] + name[idxCloser+len(closer)+1:len(name)]
        return name

    def removeNofColor(self, name):
        closer = "가지색)"
        idxCloser = name.find(closer)
        if idxCloser != -1:
            for i, cand in reversed(list(enumerate(name))):
                if i >= idxCloser:
                    continue
                if cand.isdigit():
                    continue
                idxOpener = i
                break
            name = name[0:idxOpener] + name[idxCloser+len(closer):len(name)]
        return name

    def extractPerPackage(self, name):
        perPackage = -1
        closer = "개)"
        idxCloser = name.find("개)")
        if idxCloser == -1:
            closer = "개들이)"
            idxCloser = name.find("개들이)")
        if idxCloser == -1:
            closer = "개 들이)"
            idxCloser = name.find("개 들이)")
        if idxCloser != -1:
            perPackage = name[idxCloser-2:idxCloser]
            idxOpener = perPackage.find("(")
            if idxOpener != -1:
                perPackage = perPackage[1:]
                name = name[0:idxCloser-2] + name[idxCloser+len(closer):len(name)]
            else:
                name = name[0:idxCloser-3] + name[idxCloser+len(closer):len(name)]
            return name, perPackage
        if idxCloser == -1:
            idxCloser = name.find("개")
            idxOpener = idxCloser
            for i, cand in reversed(list(enumerate(name))):
                if i >= idxCloser:
                    continue
                if cand.isdigit():
                    continue
                idxOpener = i
                break
            perPackage = name[idxOpener+1:idxCloser]
            name = name[0:idxOpener] + name[idxCloser+1:len(name)]
        return name, perPackage
    
    def getPrice(self, price):
        price = price[1:]
        price = price.replace(",",'')
        return price

    def getReviewCnt(self,rating):
        reviewCnt = rating.find_element_by_xpath("./span[2]/strong").text
        reviewCnt = reviewCnt.replace('(','')
        reviewCnt = reviewCnt.replace(')','')
        if reviewCnt == '':
            reviewCnt = '0'
        return reviewCnt
    
    def getProductImage(self, images):
        productImage = []
        for image in images:
            imageurl = image.get_attribute("src")
            productImage.append(imageurl)
        return productImage


    def getDemonstrationImage(self, imageWrapper):
        demonstrationImage = []
        try:
            images = imageWrapper.find_elements_by_tag_name("img")
            for image in images:
                demonstrationImage.append(image.get_attribute("src"))
        except:
            pass
        return demonstrationImage
    
    def getBC(self, variation):
        bc = ''
        try:
            bcVal = variation.find_element_by_id("pa_bc").get_attribute("value")
        except:
            return bc
        bc = bcVal.replace("-",".")
        bc = bc.replace("_",".")

        return bc

    def getDIA(self, variation):
        dia = ''
        try:
            diaVal = variation.find_element_by_id("pa_dia").get_attribute("value")
        except:
            return dia
        dia = diaVal.replace("-",".")
        dia = dia.replace("_",".")
        return dia

    def getPWR(self, variation):
        pwrs = []
        try:
            pwrSel = Select(self.driver.find_element_by_id('pa_pwr'))
            for option in pwrSel.options:
                pwrs.append(option.text)
            pwrs = pwrs[1:]
        except:
            pass
        
        for i, pwr in enumerate(pwrs):
            try:
                pwr = float(pwr)
            except:
                pwr = float(pwr[3:])
            pwrs[i] = pwr

        return pwrs

    def getColor(self, variation):
        colors = []
        try:
            colorSel = Select(self.driver.find_element_by_id('pa_color'))
            for option in colorSel.options:
                colors.append(option.text)
            colors = colors[1:]
        except:
            pass

        return colors

    def createLenseForEachColor(self, colors, newLense):
        name = newLense.name
        for color in colors:
            lense = copy.deepcopy(newLense)
            lense.name  = name + ' ' + color
            lense.print()
            self.lenses.append(lense)

    def getLense(self, url):
        self.driver.get(url)
        sleep(1)

        name = self.driver.find_element_by_class_name("product_title").text
        name = self.removeUsage(name)
        name = self.removeNofColor(name)
        name = self.removeStr(name,"(토릭)")
        name = self.removeStr(name,"(+ 도수상품)")
        name, perPackage = self.extractPerPackage(name)
        
        # name = self.trim(name)
        price = self.driver.find_element_by_class_name("woocommerce-Price-amount").text
        price = self.getPrice(price)

        rating = self.driver.find_element_by_class_name("star-rating")
        reviewCnt = self.getReviewCnt(rating)

        images = self.driver.find_elements_by_class_name("skip-lazy")
        productImage = self.getProductImage(images)

        variation = self.driver.find_element_by_class_name("variations")

        imageWrapper = self.driver.find_element_by_id("tab-description")
        demonstrationImage = self.getDemonstrationImage(imageWrapper)

        bc = self.getBC(variation)
        dia = self.getDIA(variation)
        pwr = self.getPWR(variation)
        color = self.getColor(variation)

        newLense = Lense(name, perPackage, price, reviewCnt, bc, dia, pwr, url, productImage,demonstrationImage)
        if len(color) != 0:
            self.createLenseForEachColor(color, newLense)
        else:
            newLense.print()
            self.lenses.append(newLense)

    def printLenses(self):
        for lense in self.lenses:
            lense.print()

    def exportLenses(self):
        with open('lenses.csv', encoding='utf-8-sig', mode='w', newline='') as csvFile:
            employee_writer = csv.writer(csvFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            employee_writer.writerow([
                'name',\
                'perPackage',\
                'price',\
                'reviewCnt',\
                'bc',\
                'dia',\
                'pwr',\
                'url',\
                'productImage',\
                'demonstrationImage'\
            ])
            for lense in self.lenses:
                employee_writer.writerow([
                    lense.name,\
                    lense.perPackage,\
                    lense.price,\
                    lense.reviewCnt,\
                    lense.bc,\
                    lense.dia,\
                    lense.pwr,\
                    lense.url,\
                    lense.productImage,\
                    lense.demonstrationImage\
                ])

class HomePage:
    def __init__(self, browser):
        self.driver = browser
        self.driver.get('https://www.lensgogo.com/')

    def go_to_lense_shelf(self):
        return LenseShelf(self.driver)

def initDriver():
    CHROMEDRIVER_PATH = '../chromedriver.exe'
    WINDOW_SIZE = "720,1080"

    chrome_options = Options()
    chrome_options.add_argument( "--headless" )
    chrome_options.add_argument( "--no-sandbox" )
    chrome_options.add_argument( "--disable-gpu" )
    chrome_options.add_argument( f"--window-size={ WINDOW_SIZE }" )
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')

    driver = webdriver.Chrome( executable_path=CHROMEDRIVER_PATH, options=chrome_options )
    return driver

def main():
    driver = initDriver()

    home_page = HomePage(driver)
    lenseshelf = home_page.go_to_lense_shelf()
    lenseshelf.getLenses()
    driver.close()

if __name__ == "__main__":
    main()