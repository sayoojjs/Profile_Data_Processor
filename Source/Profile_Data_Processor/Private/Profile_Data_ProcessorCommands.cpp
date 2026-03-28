// Copyright Epic Games, Inc. All Rights Reserved.

#include "Profile_Data_ProcessorCommands.h"

#define LOCTEXT_NAMESPACE "FProfile_Data_ProcessorModule"

void FProfile_Data_ProcessorCommands::RegisterCommands()
{
	UI_COMMAND(OpenPluginWindow, "Profile_Data_Processor", "Bring up Profile_Data_Processor window", EUserInterfaceActionType::Button, FInputChord());
}

#undef LOCTEXT_NAMESPACE
