app_name = "rb"
app_title = "rb"
app_publisher = "lotan souid"
app_description = "the new app for rb only frappe framwork"
app_email = "lotan.suid@gmail.com"
app_license = "mit"

fixtures = [
	"Custom Field",
	"Client Script",
	"Server Script",
	"Property Setter",
	"Workspace"
]


doc_events = {
	# חישוב שטח וספירת מגרשים (Lot → Plan)
	"Lot": {
		"on_update": "rb.planning.doctype.lot.lot.on_update",
		"after_delete": "rb.planning.doctype.lot.lot.after_delete"
	}
}
