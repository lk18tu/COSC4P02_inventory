from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from .models import TodoItem

print("RECIVED")

# Create your views here.
def home(request):
    print("RECIVED")
    items = TodoItem.objects.all()


    if request.method == "POST":
        title = request.POST.get("title")
        completed = request.POST.get("completed") == "on"
        quantity = request.POST.get("quantity")

        print("RECIVED nowwwwwwwwwwwwwwwww")

        # Create and save the new item
        TodoItem.objects.create(title=title, completed=completed, quantity=quantity)
        return redirect("")  # Redirect to an item list page (change as needed)
    
    return render(request, "base.html", {"todos": items})




# function to add item with html form
def add_item(request):
    items = TodoItem.objects.all()
    if request.method == "POST":
        title = request.POST.get("title")
        completed = request.POST.get("completed") == "on"
        quantity = request.POST.get("quantity")

        print("RECIVED nowwwwwwwwwwwwwwwww")

        # Create and save the new item
        TodoItem.objects.create(title=title, completed=completed, quantity=quantity)
        return redirect('home')  # Redirect to an item list page (change as needed)

    return render(request, "base.html", {"todos": items})


def delete_item(request, item_id):
    item = get_object_or_404(TodoItem, id=item_id)
    
    if request.method == "POST":  # Ensure deletion only happens on POST request
        item.delete()
        print(f"Deleted item: {item.title}")  # Debugging log
        return redirect("home")  # Redirect back to home after deletion

    return render(request, "base.html")  # Not necessary, but a fallback

