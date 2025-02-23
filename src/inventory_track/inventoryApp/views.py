from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from .models import InvItem

print("RECIVED")

# Create your views here.
def home(request):
    print("RECIVED")
    items = InvItem.objects.all()


    if request.method == "POST":
        title = request.POST.get("title")
        completed = request.POST.get("completed") == "on"
        quantity = request.POST.get("quantity")

        # Create and save the new item
        InvItem.objects.create(title=title, completed=completed, quantity=quantity)
        return redirect("")  # Redirect to an item list page (change as needed)
    
    return render(request, "base.html", {"invItems": items})




def add_item(request):
    if request.method == "POST":
        title = request.POST["title"]
        completed = "completed" in request.POST  # Checkbox handling
        quantity = request.POST["quantity"]

        # Create and save the new item
        InvItem.objects.create(title=title, completed=completed, quantity=quantity)
        return redirect("home")  # Redirect to homepage after adding

    return render(request, "add_item.html")  # Show the add form


def delete_item(request, item_id):
    item = get_object_or_404(InvItem, id=item_id)
    
    if request.method == "POST":  # Ensure deletion only happens on POST request
        item.delete()
        print(f"Deleted item: {item.title}")  # Debugging log
        return redirect("home")  # Redirect back to home after deletion

    return render(request, "base.html")  # Not necessary, but a fallback




def edit_item(request, item_id):
    item = get_object_or_404(InvItem, id=item_id)  # Fetch the item

    if request.method == "POST":
        item.title = request.POST["title"]
        item.completed = "completed" in request.POST  # Checkbox handling
        item.quantity = request.POST["quantity"]
        item.save()  # Save changes to database
        return redirect("home")  # Redirect back to homepage after update

    return render(request, "edit_item.html", {"item": item})  # Show the edit form