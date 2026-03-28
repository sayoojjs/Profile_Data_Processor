// Copyright Epic Games, Inc. All Rights Reserved.

#include "Profile_Data_ProcessorStyle.h"
#include "Styling/SlateStyleRegistry.h"
#include "Framework/Application/SlateApplication.h"
#include "Slate/SlateGameResources.h"
#include "Interfaces/IPluginManager.h"
#include "Styling/SlateStyleMacros.h"

#define RootToContentDir Style->RootToContentDir

TSharedPtr<FSlateStyleSet> FProfile_Data_ProcessorStyle::StyleInstance = nullptr;

void FProfile_Data_ProcessorStyle::Initialize()
{
	if (!StyleInstance.IsValid())
	{
		StyleInstance = Create();
		FSlateStyleRegistry::RegisterSlateStyle(*StyleInstance);
	}
}

void FProfile_Data_ProcessorStyle::Shutdown()
{
	FSlateStyleRegistry::UnRegisterSlateStyle(*StyleInstance);
	ensure(StyleInstance.IsUnique());
	StyleInstance.Reset();
}

FName FProfile_Data_ProcessorStyle::GetStyleSetName()
{
	static FName StyleSetName(TEXT("Profile_Data_ProcessorStyle"));
	return StyleSetName;
}

const FVector2D Icon16x16(16.0f, 16.0f);
const FVector2D Icon20x20(20.0f, 20.0f);

TSharedRef< FSlateStyleSet > FProfile_Data_ProcessorStyle::Create()
{
	TSharedRef< FSlateStyleSet > Style = MakeShareable(new FSlateStyleSet("Profile_Data_ProcessorStyle"));
	Style->SetContentRoot(IPluginManager::Get().FindPlugin("Profile_Data_Processor")->GetBaseDir() / TEXT("Resources"));

	Style->Set("Profile_Data_Processor.OpenPluginWindow", new IMAGE_BRUSH_SVG(TEXT("PlaceholderButtonIcon"), Icon20x20));

	return Style;
}

void FProfile_Data_ProcessorStyle::ReloadTextures()
{
	if (FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().GetRenderer()->ReloadTextureResources();
	}
}

const ISlateStyle& FProfile_Data_ProcessorStyle::Get()
{
	return *StyleInstance;
}
