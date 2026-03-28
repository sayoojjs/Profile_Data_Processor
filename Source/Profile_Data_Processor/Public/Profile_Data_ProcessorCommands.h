// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Framework/Commands/Commands.h"
#include "Profile_Data_ProcessorStyle.h"

class FProfile_Data_ProcessorCommands : public TCommands<FProfile_Data_ProcessorCommands>
{
public:

	FProfile_Data_ProcessorCommands()
		: TCommands<FProfile_Data_ProcessorCommands>(TEXT("Profile_Data_Processor"), NSLOCTEXT("Contexts", "Profile_Data_Processor", "Profile_Data_Processor Plugin"), NAME_None, FProfile_Data_ProcessorStyle::GetStyleSetName())
	{
	}

	// TCommands<> interface
	virtual void RegisterCommands() override;

public:
	TSharedPtr< FUICommandInfo > OpenPluginWindow;
};