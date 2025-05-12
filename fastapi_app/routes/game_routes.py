from fastapi import APIRouter
from fastapi import HTTPException, status
from fastapi import File, UploadFile
from core.models import Game, User, Room
from starlette.requests import ClientDisconnect
from asgiref.sync import sync_to_async
import time

from fastapi import Form, Request
from fastapi.responses import JSONResponse
from PIL import Image
from typing import Optional, List

import os
import json

import random
import string

router = APIRouter()

# In-memory store for chips coordinates (replace with DB in production)
chips_coords_store = {}

@router.get("/games/")
async def get_games(user_id: int):
    games = await sync_to_async(list)(Game.objects.filter(user_id=user_id))
    return [
        {
            "id": game.id,
            "name": game.name,
            "description": game.description,
            "date_created": game.date_created,
            "cover_image": game.picture.url,
            # add other fields as needed
        }
        for game in games
    ]

@router.get("/game/{game_id}/")
async def get_game(game_id: int):
    try:
        game = await sync_to_async(Game.objects.get)(id=game_id)
    except Game.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game with id {game_id} not found"
        )
    return {
        "game_id": game.id,
        "user_id": game.user_id,
        "title": game.name,
        "description": game.description,
        "max_users": game.max_users,
        'cover_image': game.picture.url,
        'field_image': game.map.url,
        "chips": game.chips,
        "cube": game.cube,
        "decks": game.decks,
        "objects_json": game.objects_json,
        "rules_file": game.rules.url,
    }

@router.get("/create-session/")
async def create_session(game_id: int, user_id: int):
    try:
        try:
            game = await sync_to_async(Game.objects.get)(id=game_id)
        except Game.DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Game with id {game_id} not found"
            )
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: user_id or title"
            )
        # Validate creator
        try:
            creator = await sync_to_async(User.objects.get)(id=user_id)
        except User.DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        # Generate a random room ID
        room_id = f"{''.join(random.choices(string.ascii_letters + string.digits, k=4))}-{''.join(random.choices(string.ascii_letters + string.digits, k=4))}"
        room = await sync_to_async(Room.objects.create)(
            room_id=room_id,
            name=game.name,
            description=game.description,
            max_users=game.max_users,
            picture=game.picture.url,
            map=game.map.url,
            chips=game.chips,
            cube=game.cube,
            decks=game.decks,
            objects_json=game.objects_json,
            rules=game.rules.url,
            user_id=game.user_id,
        )
        await sync_to_async(room.save)()
        return {"room_id": room_id, "detail": "Room created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("Exception occurred:", str(e))
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/session/{room_id}/")
async def get_session(room_id: str):
    try:
        room = await sync_to_async(Room.objects.get)(room_id=room_id)
    except Room.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {room_id} not found"
        )
    return {
        "room_id": room.id,
        "name": room.name,
        "description": room.description,
        "max_users": room.max_users,
        "picture": room.picture.url,
        "map": room.map.url,
        "chips": room.chips,
        "cube": room.cube,
        "decks": room.decks,
        "objects_json": room.objects_json,
        "rules": room.rules,
        "user_id": room.user_id,
        "date_created": room.date_created,
    }

@router.get("/delete-game/")
async def delete_game(game_id: int, user_id: int):
    try:
        try:
            game = await sync_to_async(Game.objects.get)(id=game_id)
        except Game.DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Game with id {game_id} not found"
            )
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: user_id or title"
            )
        # Validate creator
        try:
            creator = await sync_to_async(User.objects.get)(id=user_id)
        except User.DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        await sync_to_async(game.delete)()
        return {"detail": f"Game with id {game_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("Exception occurred:", str(e))
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
@router.post("/create-game/")
async def create_or_update_game(
    user_id: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    max_players: Optional[int] = Form(None),
    cover_image: Optional[UploadFile] = File(None),
    field_image: Optional[UploadFile] = File(None),
    chips_metadata: Optional[str] = Form(None),
    chip_files: List[UploadFile] = File([]),
    cubes_metadata: Optional[str] = Form(None),
    decks_metadata: Optional[str] = Form(None),
    deck_files: List[UploadFile] = File([]),
    game_objects_metadata: Optional[str] = Form(None),
    game_object_files: List[UploadFile] = File([]),
    rules_file: Optional[UploadFile] = File(None),
    game_id: Optional[str] = Form(None)):
    print("Creating or updating game...")
    try:
        if not user_id or not title or title.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: user_id or title"
            )

        # Validate creator
        try:
            creator = await sync_to_async(User.objects.get)(id=user_id)
        except User.DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )

        if game_id:
            # Update existing game
            try:
                game = await sync_to_async(Game.objects.get)(id=game_id)
            except Game.DoesNotExist:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Game with id {game_id} not found"
                )
            
            print(rules_file)
            game.name = title
            game.description = description
            game.max_users = max_players
            game.cube = cubes_metadata
            game.decks = decks_metadata
            game.objects_json = game_objects_metadata
            game.user_id = user_id
            if rules_file:
                dir_path = "images/games/rules"
                os.makedirs(dir_path, exist_ok=True)
                file_path = os.path.join(dir_path, f"{user_id}_{int(time.time())}_{rules_file.filename}")
                with open(file_path, "wb") as out_file:
                    out_file.write(await rules_file.read())
                game.rules = file_path
            if cover_image:
                dir_path = "images/games"
                os.makedirs(dir_path, exist_ok=True)
                # Generate a unique filename
                file_name = f"{user_id}_{int(time.time())}.jpg"
                file_path = f"{dir_path}/{file_name}.jpg"
                # Compress, resize, and save image
                image = Image.open(cover_image.file)
                image = image.convert("RGB")  # Ensure compatibility
                image.thumbnail((512, 512))  # Resize to max 512x512, keeping aspect ratio
                image.save(file_path, format="JPEG", quality=70, optimize=True)
                game.picture = file_path
            if field_image:
                dir_path = "images/games"
                os.makedirs(dir_path, exist_ok=True)
                # Generate a unique filename
                file_name = f"{user_id}_{int(time.time())}.jpg"
                file_path = f"{dir_path}/{file_name}.jpg"
                # Compress, resize, and save image
                image = Image.open(field_image.file)
                image = image.convert("RGB")  # Ensure compatibility
                image.thumbnail((1024, 1024))  # Resize to max 512x512, keeping aspect ratio
                image.save(file_path, format="JPEG", quality=70, optimize=True)
                game.map = file_path
            print("Chips metadata:", chips_metadata)
            print("Chips files:", chip_files)
            if chips_metadata:
                try:
                    chips = json.loads(chips_metadata)
                    chip_data = []
                    for chip_id, chip_info in chips.items():
                        if chip_info.get("type") == "url":
                            chip_data.append({"value": chip_info.get("value")})
                        elif chip_info.get("type") == "file":
                            # Find the corresponding file in chip_files by name
                            file_obj = next((f for f in chip_files if f.filename == chip_info.get("name")), None)
                            if file_obj:
                                dir_path = "images/games/chips"
                                os.makedirs(dir_path, exist_ok=True)
                                file_path = os.path.join(dir_path, f"{user_id}_{int(time.time())}_{file_obj.filename}")
                                image = Image.open(file_obj.file)
                                image = image.convert("RGB")  # Ensure compatibility
                                image.thumbnail((512, 512))  # Resize to max 512x512, keeping aspect ratio
                                image.save(file_path, format="PNG", quality=70, optimize=True)
                                chip_data.append({
                                    "value":file_path
                                })
                    game.chips = json.dumps(chip_data)
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid JSON format for chips metadata"
                    )

            # --- DECKS ---
            if decks_metadata:
                try:
                    decks = json.loads(decks_metadata)
                    for deck_id, deck_info in decks.items():
                        # Handle backImage
                        if deck_info.get('backImage', {}).get('type') == 'file':
                            file_obj = next((f for f in deck_files if f.filename == deck_info['backImage']['name']), None)
                            if file_obj:
                                dir_path = 'images/games/decks'
                                os.makedirs(dir_path, exist_ok=True)
                                file_path = os.path.join(dir_path, f"{user_id}_{int(time.time())}_{file_obj.filename}")
                                image = Image.open(file_obj.file)
                                image = image.convert("RGB")  # Ensure compatibility
                                image.thumbnail((512, 512))  # Resize to max 512x512, keeping aspect ratio
                                image.save(file_path, format="PNG", quality=70, optimize=True)
                                deck_info['backImage'] = {'type': 'file', 'path': file_path}
                        # Handle cards
                        for idx, card in enumerate(deck_info.get('cards', [])):
                            if card.get('type') == 'file':
                                file_obj = next((f for f in deck_files if f.filename == card['name']), None)
                                if file_obj:
                                    dir_path = 'images/games/decks/cards'
                                    os.makedirs(dir_path, exist_ok=True)
                                    file_path = os.path.join(dir_path, f"{user_id}_{int(time.time())}_{file_obj.filename}")
                                    image = Image.open(file_obj.file)
                                    image = image.convert("RGB")  # Ensure compatibility
                                    image.thumbnail((512, 512))  # Resize to max 512x512, keeping aspect ratio
                                    image.save(file_path, format="PNG", quality=70, optimize=True)
                                    deck_info['cards'][idx] = {'type': 'file', 'path': file_path}
                    game.decks = json.dumps(decks)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Invalid decks metadata: {e}")

            # --- GAME OBJECTS ---
            if game_objects_metadata:
                try:
                    game_objects = json.loads(game_objects_metadata)
                    for obj_id, obj_info in game_objects.items():
                        if obj_info.get('image', {}).get('type') == 'file':
                            file_obj = next((f for f in game_object_files if f.filename == obj_info['image']['name']), None)
                            if file_obj:
                                dir_path = 'images/games/objects'
                                os.makedirs(dir_path, exist_ok=True)
                                file_path = os.path.join(dir_path, f"{user_id}_{int(time.time())}_{file_obj.filename}")
                                with open(file_path, 'wb') as out_file:
                                    out_file.write(await file_obj.read())
                                obj_info['image'] = {'type': 'file', 'path': file_path}
                    game.objects_json = json.dumps(game_objects)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Invalid game objects metadata: {e}")

            # --- CUBES ---
            if cubes_metadata:
                try:
                    cubes = json.loads(cubes_metadata)
                    game.cube = json.dumps(cubes)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Invalid cubes metadata: {e}")

            await sync_to_async(game.save)()
            return {"game_id": game.id, "detail": "Game updated successfully"}
        else:
            # Create the game object with possible null fields
            game = await sync_to_async(Game.objects.create)(
                user_id=user_id,
                name=title,
                description=description,
                max_users=max_players,
            )
            await sync_to_async(game.save)()
            return {"game_id": game.id, "detail": "Game created successfully"}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("Exception occurred:", str(e))
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/session/{session_id}/chips/coords/")
async def get_chips_coords(session_id: int):
    # Return coordinates for all chips in this session
    return chips_coords_store.get(session_id, {})

@router.post("/session/{session_id}/chips/coords/")
async def set_chip_coords(session_id: int, request: Request):
    print(chips_coords_store)
    data = await request.json()
    idx = data.get("idx")
    left = data.get("left")
    bottom = data.get("bottom")
    if idx is None or left is None or bottom is None:
        return JSONResponse({"error": "Missing idx, left, or bottom"}, status_code=400)
    if session_id not in chips_coords_store:
        chips_coords_store[session_id] = {}
    chips_coords_store[session_id][idx] = {"left": left, "bottom": bottom}
    return {"ok": True, "coords": chips_coords_store[session_id]}