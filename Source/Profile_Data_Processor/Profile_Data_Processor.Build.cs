using UnrealBuildTool;

public class Profile_Data_Processor : ModuleRules
{
    public Profile_Data_Processor(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine"
        });

        PrivateDependencyModuleNames.AddRange(new string[]
        {
            "Slate",
            "SlateCore",
            "ApplicationCore",
            "InputCore",
            "EditorFramework",
            "UnrealEd",
            "LevelEditor",
            "ToolMenus",
            "Projects"  
        });
    }
}