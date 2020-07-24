def get_email_templates():
    return {
    	"en": {
            "uninterested": """Hey #{firstname}, 
You sent me an email about a job and I would like to follow it up.
Many roles I am offered don’t exactly fit, so I thought I would write back and attach my CV...

Thank you very much for your time, please feel free to pass my CV and this email along to whomever might be able to assist me in finding my desired role....""",
            "interested": """Hey #{firstname},
I am interested in this role, please tell me more. I have attached my CV. 
Thanks for your time,..."""
        },
        "de": {
            "uninterested": """Hey #{firstname}, 
Sie haben mir vor Kurzem eine E-Mail geschickt, auf die ich hiermit gerne zurückkommen würde.
 
Viele mir angebotene Positionen treffen nicht genau auf mich zu, so dass ich gerne die Gelegenheit nutzen möchte um näher zu erläutern, nach welcher Stelle ich suche...
 
Deshalb habe ich mich dazu entschieden Ihnen zu schreiben in der Hoffnung, dass Sie selbst oder Personen aus Ihrem Netzwerk entsprechende Positionen anzubieten haben, die zu meinem Profil passen.
 
Vielen Dank für Ihre Zeit – gerne können Sie meinen Lebenslauf und diese E-Mail an Personen weiterleiten, die mir bei der Suche nach meiner gewünschten Position behilflich sein können...""",
            "interested": """Hey #{firstname},
ich habe intresse an diese Rolle, ich möchte mehr davon erfahren. Ich habe mein Lebenslauf hinzugefügt.

LG,..."""
    }
}